import pytest
from mock import patch, MagicMock

from invenio_previewer.extensions.csv_dthreejs import validate_csv


# def validate_csv(file): 
def test_validate_csv(app):
    file = MagicMock()
    file.size = 9999

    # Exception coverage
    try:
        validate_csv(file=file)
    except:
        pass