# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

from .tasks import extract_pdf_and_update_file_contents
from .api import WekoDeposit
import pypdfium2
import os
import subprocess

def update_pdf_contents_es(record_ids):
    """register the contents of the record PDF file in elasticsearch
    Args:
        record_ids (list): List of record uuids
    """
    deposits = WekoDeposit.get_records(record_ids)
    for dep in deposits:
        file_infos = dep.get_pdf_info()
        extract_pdf_and_update_file_contents.apply_async((file_infos, str(dep.id)))

def extract_text_from_pdf(filepath, max_size):
    """Read PDF file and extract text.

    Args:
        filepath (str): Path to the PDF file.
        max_size (int): Maximum size of the extracted text in bytes.

    Returns:
        str: Extracted text from the PDF file.

    """
    reader = None
    data = ""
    try:
        reader = pypdfium2.PdfDocument(filepath)
        texts = []
        total_bytes = 0
        for page in reader:
            text = page.get_textpage().get_text_range()
            encoded = text.encode('utf-8', errors='replace')
            if total_bytes + len(encoded) > max_size:
                remain = max_size - total_bytes
                texts.append(encoded[:remain].decode('utf-8', errors='ignore'))
                break
            else:
                texts.append(text)
                total_bytes += len(encoded)
        data = "".join(texts)
        data = "".join(data.splitlines())
    finally:
        if reader is not None:
            reader.close()

    return data

def extract_text_with_tika(filepath, max_size):
    """Read non-PDF file and extract text.

    Args:
        filepath (str): Path to the PDF file.
        max_size (int): Maximum size of the extracted text in bytes.

    Raises:
        Exception: If Tika jar file does not exist.
        Exception: If Tika processing fails.

    Returns:
        str: Extracted text from the non-PDF file.
    """
    tika_jar_path = os.environ.get("TIKA_JAR_FILE_PATH")
    if not tika_jar_path or os.path.isfile(tika_jar_path) is False:
        raise Exception("not exist tika jar file.")
    args = ["java", "-jar", tika_jar_path, "-t", filepath]
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise Exception("raise in tika: {}".format(result.stderr.decode("utf-8")))
    data = "".join(result.stdout.decode("utf-8").splitlines())
    if len(data.encode('utf-8')) > max_size:
        encoded = data.encode('utf-8')
        data = encoded[:max_size].decode('utf-8', errors='ignore')

    return data
