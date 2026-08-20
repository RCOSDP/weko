# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

import xml.etree.ElementTree as ElementTree
from collections import OrderedDict

import pytest
from mock import MagicMock, patch

from weko_workflow.doi.agencies.crossref import CrossrefAgency, \
    build_batch_id, is_valid_issn, parse_submission_log
from weko_workflow.doi.agencies.crossref_mapper import normalize_item_number
from weko_workflow.doi.base import DepositResult, DepositStatus
from weko_workflow.doi.errors import DepositLogNotReadyError
from weko_workflow.doi.metadata import DoiMetadataSource
from weko_workflow.doi.orchestrator import STATUS_FAILURE, STATUS_PENDING, \
    STATUS_SUBMITTED, STATUS_SUCCESS, STATUS_UNKNOWN, request_doi_deposit, \
    run_deposit, run_poll
from weko_workflow.models import DoiDepositLog

ITEM_UUID = '0d0f0a9e-1111-4000-8000-000000000001'

CROSSREF = '{http://www.crossref.org/schema/5.4.0}'

ITEM_MAP = {
    'title.@value': ['item_title.subitem_title'],
    'title.@attributes.xml:lang': ['item_title.subitem_title_lang'],
    'creator.creatorName.@value': ['item_creator.creatorNames.creatorName'],
    'creator.creatorName.@attributes.xml:lang':
        ['item_creator.creatorNames.creatorNameLang'],
    'creator.givenName.@value': ['item_creator.givenNames.givenName'],
    'creator.givenName.@attributes.xml:lang':
        ['item_creator.givenNames.givenNameLang'],
    'creator.familyName.@value': ['item_creator.familyNames.familyName'],
    'creator.familyName.@attributes.xml:lang':
        ['item_creator.familyNames.familyNameLang'],
    'creator.nameIdentifier.@value':
        ['item_creator.nameIdentifiers.nameIdentifier'],
    'creator.nameIdentifier.@attributes.nameIdentifierScheme':
        ['item_creator.nameIdentifiers.nameIdentifierScheme'],
    'date.@value': ['item_date.subitem_date'],
    'date.@attributes.dateType': ['item_date.subitem_date_type'],
    'type.@value': ['item_type.resourcetype'],
    'description.@value': ['item_description.subitem_description'],
    'language.@value': ['item_language.subitem_language'],
    'sourceTitle.@value': ['item_source.subitem_source_title'],
    'sourceIdentifier.@value': ['item_issn.subitem_issn'],
    'sourceIdentifier.@attributes.identifierType':
        ['item_issn.subitem_issn_type'],
    'volume.@value': ['item_volume.subitem_volume'],
    'pageStart.@value': ['item_page.subitem_page_start'],
}


def _record():
    """Build item metadata holding a bilingual title and two creators."""
    return {
        'item_type_id': '15',
        'item_title': {'attribute_value_mlt': [
            {'subitem_title': 'タイトル', 'subitem_title_lang': 'ja'},
            {'subitem_title': 'The title', 'subitem_title_lang': 'en'},
        ]},
        'item_creator': {'attribute_value_mlt': [
            {'creatorNames': [
                {'creatorName': '国立情報学研究所', 'creatorNameLang': 'ja'}]},
            {'creatorNames': [
                {'creatorName': '鈴木, 花子', 'creatorNameLang': 'ja'},
                {'creatorName': 'Suzuki, Hanako', 'creatorNameLang': 'en'}],
             'familyNames': [
                 {'familyName': '鈴木', 'familyNameLang': 'ja'},
                 {'familyName': 'Suzuki', 'familyNameLang': 'en'}],
             'givenNames': [
                 {'givenName': '花子', 'givenNameLang': 'ja'},
                 {'givenName': 'Hanako', 'givenNameLang': 'en'}],
             'nameIdentifiers': [
                 {'nameIdentifier': '0000-0002-1825-0097',
                  'nameIdentifierScheme': 'ORCID'}]},
        ]},
        'item_date': {'attribute_value_mlt': [
            {'subitem_date': '2026-03-15', 'subitem_date_type': 'Issued'}]},
        'item_type': {'attribute_value_mlt': [
            {'resourcetype': 'journal article'}]},
        'item_description': {'attribute_value_mlt': [
            {'subitem_description': 'An abstract.'}]},
        'item_language': {'attribute_value_mlt': [
            {'subitem_language': 'eng'}]},
        'item_source': {'attribute_value_mlt': [
            {'subitem_source_title': 'Journal of Repository Engineering'}]},
        'item_issn': {'attribute_value_mlt': [
            {'subitem_issn': '2432-0005', 'subitem_issn_type': 'ISSN'}]},
        'item_volume': {'attribute_value_mlt': [
            {'subitem_volume': '12'}]},
        'item_page': {'attribute_value_mlt': [
            {'subitem_page_start': '101'}]},
    }


class FakeMappingData(object):
    """MappingData whose item type mapping is handed in directly."""

    def __init__(self, record, item_map):
        self.record = record
        self.item_map = item_map

    def get_data_by_mapping(self, mapping_key, ignore_empty=False,
                            hide_sub_keys=None, hide_parent_key=None):
        from weko_workflow.utils import get_item_value_in_deep

        result = OrderedDict()
        for key in self.item_map.get(mapping_key) or []:
            data = []
            split_key = key.split('.')
            attribute = self.record.get(split_key[0])
            if attribute and len(split_key) > 1:
                for value in get_item_value_in_deep(
                        attribute.get('attribute_value_mlt'),
                        split_key[1:]) or []:
                    data.append(value)
            if ignore_empty and not data:
                continue
            result[key] = data
        return result


def _source(record=None, doi='10.1234/weko.1',
            resource_url='https://weko.example.org/records/1'):
    """Build a metadata source over the fake mapping."""
    return DoiMetadataSource(
        item_uuid=ITEM_UUID, doi=doi, resource_url=resource_url,
        mapping=FakeMappingData(record if record is not None else _record(),
                                ITEM_MAP))


def _enable_crossref(app, **overrides):
    """Turn the Crossref deposits on with usable settings."""
    config = dict(
        WEKO_CROSSREF_ALLOW_REGISTER_DOI=True,
        WEKO_CROSSREF_DEPOSIT_URL='https://test.crossref.org/servlet/deposit',
        WEKO_CROSSREF_SUBMISSION_LOG_URL=(
            'https://test.crossref.org/servlet/submissionDownload'),
        WEKO_CROSSREF_LOGIN_ID='user/role',
        WEKO_CROSSREF_LOGIN_PASSWD='secret',
        WEKO_CROSSREF_DEPOSITOR_NAME='NII WEKO3',
        WEKO_CROSSREF_DEPOSITOR_EMAIL='noreply@example.org',
        WEKO_CROSSREF_REGISTRANT='National Institute of Informatics',
        WEKO_CROSSREF_RECORD_TYPE_POLICY='posted_content',
        WEKO_DOI_AGENCIES={
            '2': 'weko_workflow.doi.agencies.crossref.CrossrefAgency'},
    )
    config.update(overrides)
    app.config.update(config)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_is_valid_issn -vv -s
@pytest.mark.parametrize('value,expected', [
    ('2432-0005', True),
    ('24320005', True),
    ('2432-0000', False),
    ('0000-0002-1825-0097', False),
    ('', False),
    (None, False),
])
def test_is_valid_issn(value, expected):
    """Crossref checks the ISSN check digit, so we have to check it too."""
    assert is_valid_issn(value) is expected


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_normalize_item_number -vv -s
def test_normalize_item_number():
    """Crossref rejects an item_number longer than 32 characters."""
    assert normalize_item_number(ITEM_UUID) == \
        '0d0f0a9e111140008000000000000001'
    assert len(normalize_item_number(ITEM_UUID)) == 32


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_build_batch_id -vv -s
def test_build_batch_id():
    """The batch id carries the item and stays within Crossref's limits."""
    batch_id = build_batch_id(ITEM_UUID)
    assert batch_id.startswith('weko-0d0f0a9e111140008000000000000001-')


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_parse_submission_log_success -vv -s
def test_parse_submission_log_success():
    """A completed batch without failures is a success."""
    body = """<?xml version="1.0" encoding="UTF-8"?>
<doi_batch_diagnostic status="completed" sp="cs-test">
  <record_diagnostic status="Success">
    <doi>10.1234/weko.1</doi><msg>Successfully added</msg>
  </record_diagnostic>
</doi_batch_diagnostic>"""
    result = parse_submission_log(body, 'batch-1')
    assert result.status is DepositStatus.SUCCEEDED
    assert result.tracking_id == 'batch-1'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_parse_submission_log_failure -vv -s
def test_parse_submission_log_failure():
    """A failed record diagnostic is definitive and keeps its message."""
    body = """<?xml version="1.0" encoding="UTF-8"?>
<doi_batch_diagnostic status="completed" sp="cs-test">
  <record_diagnostic status="Failure" msg_id="21">
    <doi>all doi's under the current journal element</doi>
    <msg>ISSN "24320000" is invalid </msg>
  </record_diagnostic>
</doi_batch_diagnostic>"""
    result = parse_submission_log(body, 'batch-1')
    assert result.status is DepositStatus.FAILED
    assert 'ISSN' in result.message


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_parse_submission_log_pending -vv -s
@pytest.mark.parametrize('status', ['in_process', 'queued',
                                    'unknown_submission'])
def test_parse_submission_log_pending(status):
    """Crossref answers unknown_submission while the batch is queued."""
    body = '<doi_batch_diagnostic status="{0}"><submission_id>0' \
           '</submission_id></doi_batch_diagnostic>'.format(status)
    assert parse_submission_log(body, 'batch-1').status \
        is DepositStatus.ACCEPTED


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_parse_submission_log_garbage -vv -s
def test_parse_submission_log_garbage():
    """An answer that is not the expected XML is worth another try."""
    assert parse_submission_log('Cannot authenticate user', 'b').status \
        is DepositStatus.RETRIABLE
    assert parse_submission_log('<html><body>oops</body></html>', 'b').status \
        is DepositStatus.RETRIABLE


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_is_allowed -vv -s
def test_is_allowed(app):
    """A missing setting must never look like "registration is off"."""
    agency = CrossrefAgency()
    with app.app_context():
        app.config['WEKO_CROSSREF_ALLOW_REGISTER_DOI'] = False
        assert agency.is_allowed() is False

        _enable_crossref(app)
        assert agency.is_allowed() is True

        app.config['WEKO_CROSSREF_LOGIN_PASSWD'] = None
        assert agency.is_allowed() is False


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_metadata_source -vv -s
def test_metadata_source(app):
    """Multilingual values collapse to what Crossref can hold."""
    with app.app_context():
        source = _source()
        assert ('The title', 'en') in source.titles()
        assert source.language() == 'en'
        assert source.publication_date() == {
            'year': 2026, 'month': 3, 'day': 15}
        assert source.resource_type() == 'journal article'
        assert source.journal()['issn'] == '2432-0005'

        creators = source.creators()
        assert len(creators) == 2
        assert creators[0]['surname'] == '国立情報学研究所'
        assert creators[0]['given'] is None
        assert creators[1]['surname'] == 'Suzuki'
        assert creators[1]['given'] == 'Hanako'
        assert creators[1]['orcid'] == 'https://orcid.org/0000-0002-1825-0097'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_build_payload_posted_content -vv -s
def test_build_payload_posted_content(app):
    """Everything is deposited as posted_content by default."""
    with app.app_context():
        _enable_crossref(app)
        request = CrossrefAgency().build_payload(_source())

        assert request.record_type == 'posted_content'
        assert request.payload.startswith('<?xml')

        # parsed rather than matched: Python 3.6 sorts the attributes
        root = ElementTree.fromstring(request.payload)
        posted = root.find('{0}body/{0}posted_content'.format(CROSSREF))
        assert posted.get('type') == 'other'
        assert posted.get('language') == 'en'
        assert posted.find('{0}titles/{0}title'.format(CROSSREF)).text \
            == 'The title'
        assert posted.find(
            '{0}titles/{0}original_language_title'.format(CROSSREF)).text \
            == 'タイトル'
        assert posted.find('{0}item_number'.format(CROSSREF)).text \
            == '0d0f0a9e111140008000000000000001'
        assert posted.find('{0}doi_data/{0}doi'.format(CROSSREF)).text \
            == '10.1234/weko.1'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_build_payload_journal_article -vv -s
def test_build_payload_journal_article(app):
    """The auto policy follows the resource type when it can."""
    with app.app_context():
        _enable_crossref(app, WEKO_CROSSREF_RECORD_TYPE_POLICY='auto')
        request = CrossrefAgency().build_payload(_source())

        assert request.record_type == 'journal_article'
        assert '<full_title>Journal of Repository Engineering</full_title>' \
            in request.payload
        assert '<issn media_type="electronic">2432-0005</issn>' \
            in request.payload


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_build_payload_falls_back_without_journal -vv -s
def test_build_payload_falls_back_without_journal(app):
    """A journal article without a journal title stays posted_content."""
    record = _record()
    del record['item_source']
    with app.app_context():
        _enable_crossref(app, WEKO_CROSSREF_RECORD_TYPE_POLICY='auto')
        request = CrossrefAgency().build_payload(_source(record))
        assert request.record_type == 'posted_content'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_validate -vv -s
def test_validate(app):
    """What Crossref checks beyond the schema is checked before sending."""
    with app.app_context():
        _enable_crossref(app, WEKO_CROSSREF_RECORD_TYPE_POLICY='auto')
        agency = CrossrefAgency()
        assert agency.validate(_source()) == []

        record = _record()
        del record['item_date']
        record['item_issn']['attribute_value_mlt'][0]['subitem_issn'] = \
            '2432-0000'
        errors = agency.validate(_source(record))
        assert len(errors) == 2
        assert any('date' in error for error in errors)
        assert any('ISSN' in error for error in errors)

        errors = agency.validate(_source(doi='', resource_url='/records/1'))
        assert len(errors) == 2

        # the identifier settings screen leaves "<Empty>" when the Crossref
        # prefix was never configured
        errors = agency.validate(_source(doi='<Empty>/2000001'))
        assert len(errors) == 1
        assert 'prefix' in errors[0]


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_register -vv -s
def test_register(app):
    """The deposit servlet only ever answers "received"."""
    with app.app_context():
        _enable_crossref(app)
        agency = CrossrefAgency()
        request = agency.build_payload(_source())

        with patch('weko_workflow.doi.agencies.crossref.requests.post',
                   return_value=MagicMock(
                       status_code=200,
                       text='<html><head><title>SUCCESS</title></head>'
                            '</html>')):
            result = agency.register(request)
        assert result.status is DepositStatus.ACCEPTED
        assert result.tracking_id == request.tracking_id

        with patch('weko_workflow.doi.agencies.crossref.requests.post',
                   return_value=MagicMock(status_code=503, text='busy')):
            assert agency.register(request).status is DepositStatus.RETRIABLE

        with patch('weko_workflow.doi.agencies.crossref.requests.post',
                   return_value=MagicMock(status_code=401, text='denied')):
            assert agency.register(request).status is DepositStatus.FAILED


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_register_unreachable -vv -s
def test_register_unreachable(app):
    """A network error is temporary, never a rejection."""
    import requests

    with app.app_context():
        _enable_crossref(app)
        agency = CrossrefAgency()
        request = agency.build_payload(_source())
        with patch('weko_workflow.doi.agencies.crossref.requests.post',
                   side_effect=requests.exceptions.Timeout('timed out')):
            assert agency.register(request).status is DepositStatus.RETRIABLE


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_poll -vv -s
def test_poll(app):
    """Polling reads the submission log of one batch."""
    body = '<doi_batch_diagnostic status="completed">' \
           '<record_diagnostic status="Success"><doi>10.1234/weko.1</doi>' \
           '<msg>Successfully added</msg></record_diagnostic>' \
           '</doi_batch_diagnostic>'
    with app.app_context():
        _enable_crossref(app)
        with patch('weko_workflow.doi.agencies.crossref.requests.get',
                   return_value=MagicMock(status_code=200, text=body)):
            assert CrossrefAgency().poll('batch-1').status \
                is DepositStatus.SUCCEEDED


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_request_doi_deposit_is_skipped -vv -s
def test_request_doi_deposit_is_skipped(app, db):
    """Nothing is written when the agency is unknown or turned off."""
    with app.app_context():
        _enable_crossref(app)
        # JaLC has no agency yet
        assert request_doi_deposit(ITEM_UUID, '1', '10.1234/weko.1') is None

        app.config['WEKO_CROSSREF_ALLOW_REGISTER_DOI'] = False
        assert request_doi_deposit(ITEM_UUID, '2', '10.1234/weko.1') is None
        assert DoiDepositLog.query.count() == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_request_doi_deposit_creates_log -vv -s
def test_request_doi_deposit_creates_log(app, db):
    """The request only writes the log; the deposit itself is a task."""
    with app.app_context():
        _enable_crossref(app)
        with patch('weko_workflow.doi.tasks.deposit_doi.apply_async') \
                as task:
            log = request_doi_deposit(
                ITEM_UUID, '2', '10.1234/weko.1',
                resource_url='https://weko.example.org/records/1')

        assert log is not None
        assert log.deposit_status == STATUS_PENDING
        assert log.agency == 'Crossref'
        assert log.doi == '10.1234/weko.1'
        task.assert_called_once()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_request_doi_deposit_never_raises -vv -s
def test_request_doi_deposit_never_raises(app, db):
    """A broken agency must not break the item registration."""
    with app.app_context():
        _enable_crossref(app)
        with patch('weko_workflow.doi.orchestrator.get_agency',
                   side_effect=Exception('boom')):
            assert request_doi_deposit(ITEM_UUID, '2', '10.1') is None


def _pending_log(db, **overrides):
    """Store a log row to run the orchestrator against."""
    values = dict(
        item_uuid=ITEM_UUID, agency='Crossref', doi_select='2',
        doi='10.1234/weko.1',
        resource_url='https://weko.example.org/records/1',
        deposit_status=STATUS_PENDING)
    values.update(overrides)
    log = DoiDepositLog(**values)
    db.session.add(log)
    db.session.commit()
    return log


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_run_deposit_accepted -vv -s
def test_run_deposit_accepted(app, db):
    """An accepted deposit waits for the polling to judge it."""
    with app.app_context():
        _enable_crossref(app)
        log = _pending_log(db)
        with patch('weko_workflow.doi.orchestrator.DoiMetadataSource',
                   return_value=_source()), \
            patch('weko_workflow.doi.agencies.crossref.requests.post',
                  return_value=MagicMock(status_code=200, text='SUCCESS')):
            status = run_deposit(log.id)

        assert status is DepositStatus.ACCEPTED
        assert log.deposit_status == STATUS_SUBMITTED
        assert log.payload.startswith('<?xml')
        assert '<doi_batch' in log.payload
        assert log.attempt == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_run_deposit_rejects_invalid_metadata -vv -s
def test_run_deposit_rejects_invalid_metadata(app, db):
    """Metadata Crossref would reject never reaches the network."""
    record = _record()
    del record['item_date']
    with app.app_context():
        _enable_crossref(app)
        log = _pending_log(db)
        with patch('weko_workflow.doi.orchestrator.DoiMetadataSource',
                   return_value=_source(record)), \
            patch('weko_workflow.doi.agencies.crossref.requests.post') \
                as post:
            status = run_deposit(log.id)

        assert status is DepositStatus.FAILED
        assert log.deposit_status == STATUS_FAILURE
        assert 'date' in log.error_message
        post.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_run_deposit_without_log -vv -s
def test_run_deposit_without_log(app, db):
    """A task started before the commit is asked to come back later."""
    with app.app_context():
        _enable_crossref(app)
        with pytest.raises(DepositLogNotReadyError):
            run_deposit(999999)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_run_poll_success -vv -s
def test_run_poll_success(app, db):
    """A successful poll closes the deposit."""
    body = '<doi_batch_diagnostic status="completed">' \
           '<record_diagnostic status="Success"><doi>10.1234/weko.1</doi>' \
           '<msg>Successfully added</msg></record_diagnostic>' \
           '</doi_batch_diagnostic>'
    with app.app_context():
        _enable_crossref(app)
        log = _pending_log(db, deposit_status=STATUS_SUBMITTED,
                           tracking_id='batch-1')
        with patch('weko_workflow.doi.agencies.crossref.requests.get',
                   return_value=MagicMock(status_code=200, text=body)):
            status = run_poll(log.id)

        assert status is DepositStatus.SUCCEEDED
        assert log.deposit_status == STATUS_SUCCESS


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_doi.py::test_run_poll_gives_up -vv -s
def test_run_poll_gives_up(app, db):
    """Polling stops instead of running forever on a stuck submission."""
    with app.app_context():
        _enable_crossref(app, WEKO_DOI_MAX_POLL_ATTEMPTS=2)
        log = _pending_log(db, deposit_status=STATUS_SUBMITTED,
                           tracking_id='batch-1', poll_attempt=2)
        with patch('weko_workflow.doi.agencies.crossref.requests.get') as get:
            run_poll(log.id)

        assert log.deposit_status == STATUS_UNKNOWN
        get.assert_not_called()
