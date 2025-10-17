import os
import json
import copy
import uuid
from datetime import date
from os.path import dirname, join
import bagit
from bagit import open_text_file

from invenio_db import db
from invenio_records import Record
from weko_records.api import ItemsMetadata, WekoRecord
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from weko_deposit.api import WekoDeposit
from invenio_pidrelations.models import PIDRelation

def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


def create_record(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()

        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent = None
        doi = None
        if not ('.' in record_data["recid"]):
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent,recid,2,0)
            db.session.add(rel)
            doi = PersistentIdentifier.create('doi', " https://doi.org/10.xyz/{}".format((str(record_data["recid"])).zfill(10)),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        else:
            parent = PersistentIdentifier.get('parent','parent:{}'.format((str(record_data["recid"])).split('.')[0]))
            rel = PIDRelation.create(parent,recid,2,(str(record_data["recid"])).split('.')[1])
            db.session.add(rel)

        record = WekoRecord.create(record_data, id_=rec_uuid)
        deposit = WekoDeposit(record, record.model)

        deposit.commit()

        item = ItemsMetadata.create(item_data, id_=rec_uuid)

    return depid, recid,parent,doi,record, item



def bagify(
    bag_dir, bag_info=None, processes=1, checksums=None, encoding="utf-8"
):
    """ Give manifests.

    Give tag files and manifests to an existing directory.
    It is required that the given directory contains data in data/.
    If the directory does not have data/, use the bagit.make_bag function.

    Args:
        bag_dir (str): The directory to bag.
        bag_info (dict): A dictionary of tag file values.
        processes (int): The number of processes to use when creating manifests.
        checksums (list of str): The checksum algorithms to use when creating manifests.
        encoding (str): The encoding to use when creating tag files.

    Returns:
        Bag: The bag created from the given directory.
    """

    if checksums is None:
        checksums = bagit.DEFAULT_CHECKSUMS

    bag_dir = os.path.abspath(bag_dir)
    cwd = os.path.abspath(os.path.curdir)

    if cwd.startswith(bag_dir) and cwd != bag_dir:
        raise RuntimeError("Bagging a parent of the current directory is not supported")

    bagit.LOGGER.info("Creating tag for directory %s", bag_dir)

    if not os.path.isdir(bag_dir):
        bagit.LOGGER.error("Bag directory %s does not exist", bag_dir)
        raise RuntimeError("Bag directory %s does not exist" % bag_dir)

    old_dir = os.path.abspath(os.path.curdir)

    if not os.path.exists(os.path.join(bag_dir, "data")):
        bagit.LOGGER.error("Bag directory %s does not contain a data directory", bag_dir)
        raise RuntimeError("Bag directory %s does not contain a data directory" % bag_dir)

    try:
        unbaggable = bagit._can_bag(bag_dir)

        if unbaggable:
            bagit.LOGGER.error(
                "Unable to write to the following directories and files:\n%s",
                unbaggable,
            )
            raise bagit.BagError("Missing permissions to move all files and directories")

        unreadable_dirs, unreadable_files = bagit._can_read(bag_dir)

        if unreadable_dirs or unreadable_files:
            if unreadable_dirs:
                bagit.LOGGER.error(
                    "The following directories do not have read permissions:\n%s",
                    unreadable_dirs,
                )
            if unreadable_files:
                bagit.LOGGER.error(
                    "The following files do not have read permissions:\n%s",
                    unreadable_files,
                )
            raise bagit.BagError(
                "Read permissions are required to calculate file fixities"
            )
        else:
            bagit.LOGGER.info("Creating data directory")

            os.chdir(bag_dir)
            cwd = os.getcwd()

            # permissions for the payload directory should match those of the
            # original directory
            os.chmod("data", os.stat(cwd).st_mode)

            for algorithm in checksums:
                manifest_filename = "manifest-%s.txt" % algorithm
                with open_text_file(manifest_filename, "w", encoding=encoding) as manifest_file:
                    pass
            total_bytes, total_files = bagit.make_manifests(
                "data", processes, algorithms=checksums, encoding=encoding
            )

            bagit.LOGGER.info("Creating bagit.txt")
            txt = """BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n"""
            with bagit.open_text_file("bagit.txt", "w") as bagit_file:
                bagit_file.write(txt)

            bagit.LOGGER.info("Creating bag-info.txt")
            if bag_info is None:
                bag_info = {}

            # allow 'Bagging-Date' and 'Bag-Software-Agent' to be overidden
            if "Bagging-Date" not in bag_info:
                bag_info["Bagging-Date"] = "2025-06-10"
            if "Bag-Software-Agent" not in bag_info:
                bag_info["Bag-Software-Agent"] = "bagit.py v%s <%s>" % (
                    bagit.VERSION,
                    bagit.PROJECT_URL,
                )

            bag_info["Payload-Oxum"] = "%s.%s" % (total_bytes, total_files)
            bagit._make_tag_file("bag-info.txt", bag_info)

            for algorithm in checksums:
                bagit._make_tagmanifest_file(algorithm, bag_dir, encoding="utf-8")
    except Exception:
        bagit.LOGGER.exception("An error occurred creating a bag in %s", bag_dir)
        raise
    finally:
        os.chdir(old_dir)

    return bagit.Bag(bag_dir)
