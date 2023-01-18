import json
import copy
from unittest.mock import Mock
import uuid
from os.path import dirname, join


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)