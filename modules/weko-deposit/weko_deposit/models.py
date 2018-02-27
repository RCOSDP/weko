# # -*- coding: utf-8 -*-
# #
# # This file is part of WEKO3.
# # Copyright (C) 2017 National Institute of Informatics.
# #
# # WEKO3 is free software; you can redistribute it
# # and/or modify it under the terms of the GNU General Public License as
# # published by the Free Software Foundation; either version 2 of the
# # License, or (at your option) any later version.
# #
# # WEKO3 is distributed in the hope that it will be
# # useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# # General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with WEKO3; if not, write to the
# # Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# # MA 02111-1307, USA.
#
# """Weko Deposit Model."""
#
# import uuid
#
# from invenio_files_rest.models import FileInstance, ObjectVersion
# from invenio_db import db
# from sqlalchemy.dialects import postgresql
# from sqlalchemy_utils.types import JSONType
#
#
# class WekoFileInstance(FileInstance):
#     """Model for storing files.
#
#     A file instance represents a file on disk. A file instance may be linked
#     from many objects, while an object can have one and only one file instance.
#
#     A file instance also records the storage class, size and checksum of the
#     file on disk.
#
#     Additionally, a file instance can be read only in case the storage layer
#     is not capable of writing to the file (e.g. can typically be used to
#     link to files on externally controlled storage).
#     """
#
#     # __tablename__ = 'files_files'
#
#     # __table_args__ = {'extend_existing': True}
#
#     __mapper_args__ = {'polymorphic_identity': 'WekoFileInstance'}
#
#     json = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )
#
#     def update_json(self, jsn):
#         """
#         update file metadata
#         :param jsn: Dictionary of file metadata.
#         :return:
#         """
#         self.json = jsn
#
#     def upload_file(self, fjson, id, uuid, index, doc_type, **kwargs):
#         """
#           Put file to Elasticsearch
#         :param fjson:
#         :param id:
#         :param uuid:
#         :param index:
#         :param doc_type:
#         :param kwargs:
#         """
#         self.storage(**kwargs).upload_file(fjson, id, uuid, index, doc_type)
#
#
# class WekoObjectVersion(ObjectVersion):
#     """ObjectVersion extend."""
#
#     # __tablename__ = 'files_object'
#
#     # __table_args__ = {'extend_existing': True}
#
#     __mapper_args__ = {'polymorphic_identity': 'WekoObjectVersion'}
#
#     file = db.relationship(WekoFileInstance, backref='obj')
#     """Relationship to file instance."""
#
#
# __all__ = (
#     'WekoFileInstance',
#     'WekoObjectVersion',
# )
