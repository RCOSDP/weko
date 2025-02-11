import json
import pytest
from weko_search_ui.mapper import JsonLdMapper

from .helpers import json_data


# def JsonLdMapper:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestJsonLdMapper:
    # def process_json_ld(json_ld):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper::test_process_json_ld -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_process_json_ld(self, app):
        app.config.update({"WEKO_SWORDSERVER_METADATA_FILE_ROCRATE": "ro-crate-metadata.json"})

        json_ld = json_data("data/ro-crate/ro-crate-metadata.json")
        processed_metadata, format = JsonLdMapper.process_json_ld(json_ld)

        assert format == "ro-crate"
        assert processed_metadata["@id"] == "./"
        assert processed_metadata["name"] == "The Sample Dataset for WEKO"
        assert processed_metadata["description"] == "This is a sample dataset for WEKO in order to demonstrate the RO-Crate metadata."
        assert processed_metadata["dc:title[0].value"] == "The Sample Dataset for WEKO"
        assert processed_metadata["dc:title[0].language"] == "en"
        assert processed_metadata["creator[0].affiliation.name"] == "University of Manchester"
        assert processed_metadata["hasPart[0].@id"] == "data/sample.rst"
        assert processed_metadata["hasPart[0].name"] == "sample.rst"
        assert processed_metadata["hasPolicy[0].permission[0].duty[0].assignee"] == "http://example.org/rightsholder"
        assert processed_metadata["wk:saveAsIs"] == False
        assert not any("@type" in key for key in processed_metadata.keys())
