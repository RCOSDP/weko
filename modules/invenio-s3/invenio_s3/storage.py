# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage interface."""
from __future__ import absolute_import, print_function
import os ,pathlib
import shutil
from tempfile import SpooledTemporaryFile
import boto3
import traceback
import uuid
import s3fs
from flask import current_app
from invenio_files_rest.models import Location, Part
from invenio_files_rest.errors import StorageError
from invenio_files_rest.storage import PyFSFileStorage, pyfs_storage_factory

from .config import S3_SEND_FILE_DIRECTLY
from .helpers import redirect_stream


class S3FSFileStorage(PyFSFileStorage):
    """File system storage using Amazon S3 API for accessing files."""

    def __init__(self, fileurl, **kwargs):
        """Storage initialization."""
        super(S3FSFileStorage, self).__init__(fileurl, **kwargs)

    def _get_fs(self, *args, **kwargs):
        """Ge PyFilesystem instance and S3 real path."""
        if not self.fileurl.startswith('s3://'):
            return super(S3FSFileStorage, self)._get_fs(*args, **kwargs)

        info = current_app.extensions['invenio-s3'].init_s3f3_info
        fs = s3fs.S3FileSystem(**info)

        return (fs, self.fileurl)

    def initialize(self, size=0):
        """Initialize file on storage and truncate to given size."""
        fs, path = self._get_fs()

        self.remove(fs, path)
        fp = fs.open(path, mode='wb')

        try:
            to_write = size
            fs_chunk_size = fp.blocksize  # Force write every time
            while to_write > 0:
                current_chunk_size = (to_write if to_write <= fs_chunk_size
                                      else fs_chunk_size)
                fp.write(b'\0' * current_chunk_size)
                to_write -= current_chunk_size
        except Exception:
            traceback.format_exc()
            fp.close()
            self.delete()
            raise
        finally:
            fp.close()

        self._size = size

        return self.fileurl, size, None

    def initiateMultipartUpload(self, bucket_name:str ,object_name ,buket_type:str):
        bucket_type_s3 = current_app.config['FILES_REST_LOCATION_TYPE_LIST'][0][0]
        if bucket_type_s3 == buket_type:
            s3 = self.get_s3_client()
            bucket_nm = bucket_name.replace("s3://" ,"").split("/")[0]
            # organ_nm = bucket_name.replace("s3://" ,"").split("/")[1]
            res = s3.create_multipart_upload(
                Bucket=bucket_nm
                ,Key=self.fileurl.replace("s3://" + bucket_nm + "/","")
            )

            upload_id = res['UploadId']
            return self.fileurl, upload_id

        else :
            # local file
            upload_id = uuid.uuid4()
            
            path = pathlib.Path(bucket_name).joinpath(self.fileurl.replace("/data" ,"")).joinpath(str(upload_id))
            os.makedirs(name=str(path))

            return self.fileurl, upload_id

    def get_s3_client(self):
        
        s3client = boto3.client(
            's3'
            ,aws_access_key_id=current_app.config['S3_ACCCESS_KEY_ID']
            ,aws_secret_access_key=current_app.config['S3_SECRECT_ACCESS_KEY']
            ,region_name=current_app.config['S3_REGION_NAME']
            ,endpoint_url=current_app.config['S3_ENDPOINT_URL']
        )

        return s3client

    def remove(self, fs, path):
        """Delete a file with check FS."""
        if fs.exists(path):
            if isinstance(fs, s3fs.S3FileSystem):
                fs.rm(path)
            else:
                fs.remove(path)

    def delete(self):
        """Delete a file."""
        fs, path = self._get_fs()
        self.remove(fs, path)
        return True
    
    def upload_multipart(self
                , object_name :str
                , incoming_stream :SpooledTemporaryFile
                , bucket_name:str
                , part_number:int
                , upload_id:uuid.UUID
                , buket_type:str
                ):
        """Update a file in the file system."""
        """
        PartNumber : 0~9999
        """

        bucket_type_s3 = current_app.config['FILES_REST_LOCATION_TYPE_LIST'][0][0]
        if bucket_type_s3 == buket_type:

            s3 = self.get_s3_client()

            bucket_nm = bucket_name.replace("s3://" ,"").split("/")[0]
            res = s3.upload_part(
                Key=self.fileurl.replace("s3://" + bucket_nm + "/","")
                ,Body=incoming_stream
                ,Bucket=bucket_nm
                ,PartNumber=part_number + 1
                ,UploadId=str(upload_id)
            )

            etag = res['ETag']

            return etag
        
        else :
            # local file
            path = pathlib.Path(bucket_name).joinpath(self.fileurl.replace("/data" ,"")).joinpath(str(upload_id)).joinpath(str(part_number))
            path.touch()
            with path.open(mode='wb') as con :
                con.write(incoming_stream.read())

            return upload_id

    def complete_multipart_upload(self
    
                , object_name :str
                , bucket_name:str
                , upload_id:uuid.UUID
                , parts
                , buket_type:str
                ):
        bucket_type_s3 = current_app.config['FILES_REST_LOCATION_TYPE_LIST'][0][0]
        if bucket_type_s3 == buket_type:
            s3 = self.get_s3_client()
            li = []
            for part in parts:
                li.append({
                    'PartNumber': part.part_number + 1,
                    'ETag': part.etag
                })
            multipart_upload = {'Parts': li}
            bucket_nm = bucket_name.replace("s3://" ,"").split("/")[0]
            res = s3.complete_multipart_upload(
                Key=self.fileurl.replace("s3://" + bucket_nm + "/" ,"")
                ,Bucket=bucket_nm
                ,UploadId=str(upload_id)
                ,MultipartUpload=multipart_upload
            )
            return res
        else :
            # local file
            path_tmp = pathlib.Path(bucket_name).joinpath(self.fileurl.replace("/data" ,"")).joinpath(str(upload_id))
            path_data = pathlib.Path(self.fileurl)
            path_data.touch(exist_ok=True)

            listdir = os.listdir(str(path_tmp))
            with path_data.open("wb") as con:
                for file in listdir:
                    with path_tmp.joinpath(file).open("rb") as con_tmp:
                        con.write(con_tmp.read())
            shutil.rmtree(path_tmp)

            return True

    def update(self,
               incoming_stream,
               seek=0,
               size=None,
               chunk_size=None,
               progress_callback=None):
        """Update a file in the file system."""
        old_fp = self.open(mode='rb')
        updated_fp = S3FSFileStorage(
            self.fileurl, size=self._size).open(mode='wb')
        try:
            if seek >= 0:
                to_write = seek
                fs_chunk_size = updated_fp.blocksize
                while to_write > 0:
                    current_chunk_size = (to_write if to_write <= fs_chunk_size
                                          else fs_chunk_size)
                    updated_fp.write(old_fp.read(current_chunk_size))
                    to_write -= current_chunk_size

            bytes_written, checksum = self._write_stream(
                incoming_stream,
                updated_fp,
                chunk_size=chunk_size,
                size=size,
                progress_callback=progress_callback)

            if (bytes_written + seek) < self._size:
                old_fp.seek((bytes_written + seek))
                to_write = self._size - (bytes_written + seek)
                fs_chunk_size = updated_fp.blocksize
                while to_write > 0:
                    current_chunk_size = (to_write if to_write <= fs_chunk_size
                                          else fs_chunk_size)
                    updated_fp.write(old_fp.read(current_chunk_size))
                    to_write -= current_chunk_size
        finally:
            old_fp.close()
            updated_fp.close()

        return bytes_written, checksum

    def send_file(self, filename, mimetype=None, restricted=True, checksum=None,
                  trusted=False, chunk_size=None, as_attachment=False):
        """Send the file to the client."""
        s3_send_file_directly = current_app.config.get('S3_SEND_FILE_DIRECTLY', None)
        default_location = Location.query.filter_by(default=True).first()

        if default_location.type == 's3':
            s3_send_file_directly = default_location.s3_send_file_directly

        if s3_send_file_directly:
            return super(S3FSFileStorage, self).send_file(filename,
                                                          mimetype=mimetype,
                                                          restricted=restricted,
                                                          checksum=checksum,
                                                          trusted=trusted,
                                                          chunk_size=chunk_size,
                                                          as_attachment=as_attachment)
        try:
            fs, path = self._get_fs()
            url = fs.url(path, expires=60)

            md5_checksum = None
            if checksum:
                algo, value = checksum.split(':')
                if algo == 'md5':
                    md5_checksum = value

            return redirect_stream(
                url,
                filename,
                self._size,
                self._modified,
                mimetype=mimetype,
                restricted=restricted,
                etag=checksum,
                content_md5=md5_checksum,
                chunk_size=chunk_size,
                trusted=trusted,
                as_attachment=as_attachment,
            )
        except Exception as e:
            traceback.format_exc()
            raise StorageError('Could not send file: {}'.format(e))

    def copy(self, src, *args, **kwargs):
        """Copy data from another file instance.

        If the source is an S3 stored object the copy process happens on the S3
        server side, otherwise we use the normal ``FileStorage`` copy method.
        """
        if src.fileurl.startswith('s3://'):
            fs, path = self._get_fs()
            fs.copy(src.fileurl, path)
        else:
            super(S3FSFileStorage, self).copy(src, *args, **kwargs)


def s3fs_storage_factory(**kwargs):
    """File storage factory for S3."""
    return pyfs_storage_factory(filestorage_class=S3FSFileStorage, **kwargs)
