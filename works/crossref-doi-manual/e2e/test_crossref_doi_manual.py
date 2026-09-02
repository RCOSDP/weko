"""Walk the Crossref DOI registration flow and capture the manual's images.

This is a capture script shaped as a test: every step both asserts that the
application still behaves as the manual describes and leaves a screenshot
behind in ``works/crossref-doi-manual/images``.  The steps run in order and
share one page, because WEKO locks a workflow activity to the session that
opened it.

Run it against a stack started with ``e2e/compose.e2e.yml``; see the README
next to this file.
"""

import os
import re
import tempfile
import time

# Crossref's documented example prefix; the stub accepts any well formed DOI,
# and a real repository uses the prefix Crossref issued it.
CROSSREF_PREFIX = os.getenv('WEKO_CROSSREF_TEST_PREFIX', '10.5555')

ITEM_TYPE = '30002'
"""Item type the default full workflow registers, used in every field name."""

TITLE = 'Registering a Crossref DOI from WEKO3'
JOURNAL_TITLE = 'Journal of WEKO Studies'
ISSN = '0317-8471'
"""A structurally valid ISSN: WEKO checks the check digit before depositing."""

PUB_DATE = '2026-09-02'

INDEX_NAME = os.getenv('WEKO_TEST_INDEX', 'Sample Index')

SAMPLE_PDF = (
    b'%PDF-1.4\n'
    b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
    b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
    b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 100]'
    b'/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n'
    b'4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n'
    b'5 0 obj<</Length 62>>stream\n'
    b'BT /F1 12 Tf 20 50 Td (WEKO3 Crossref DOI sample) Tj ET\n'
    b'endstream endobj\n'
    b'trailer<</Root 1 0 R>>\n'
)
"""A one page PDF, so the item has the file a DOI grant requires."""


def sample_file():
    """Write the sample PDF to a temporary file and return its path."""
    path = os.path.join(tempfile.mkdtemp(), 'weko-crossref-sample.pdf')
    with open(path, 'wb') as handle:
        handle.write(SAMPLE_PDF)
    return path


# -- helpers ---------------------------------------------------------------

def field(page, name):
    """Return the visible control of an item metadata field.

    The item form is a set of collapsible panels, so a field is invisible
    until its panel is open; this opens the panel holding the field the first
    time the field is asked for.  It also skips the hidden copy the form keeps
    of every field as the "add another" template.

    :param page: playwright page
    :param name: form control name, e.g. ``item_30002_title0.0.subitem_title``
    :return: locator of the visible control
    """
    escaped = name.replace('.', '\\.')
    control = page.locator(
        "input[name='{0}'], select[name='{0}'], textarea[name='{0}']".format(
            escaped))
    visible = control.locator('visible=true')
    if not visible.count():
        control.first.evaluate(
            "el => {const panel = el.closest('.panel');"
            " const toggle = panel && panel.querySelector('a.panel-toggle');"
            " if (toggle) toggle.click();}")
        page.wait_for_timeout(800)
        visible = control.locator('visible=true')
    return visible.first


def force_unlock(page):
    """Take over an activity another session left open, when asked to.

    WEKO locks an activity to the session that opened it; a capture that was
    interrupted leaves the lock behind and the next run has to take it over.
    """
    button = page.locator('#user_locked_btn')
    if button.count() and button.first.is_visible():
        button.first.click()
        page.locator('#btn_unlock').first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(6000)


def quit_open_activity(page, base_url):
    """Quit the activity WEKO says is already open, if it named one.

    One user may hold one activity at a time, so a run that did not reach the
    end blocks the next one until its activity is quit.

    :return: the activity id that was quit, or None
    """
    match = re.search(r'Already have another activity open \((A-[0-9\-]+)\)',
                      page.locator('body').inner_text())
    if not match:
        return None
    activity_id = match.group(1)
    page.goto('{0}/workflow/activity/detail/{1}'.format(base_url, activity_id))
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(4000)
    force_unlock(page)
    page.locator('#btn_quit').locator('visible=true').first.click()
    page.wait_for_timeout(1000)
    page.locator('#btn_cancel').locator('visible=true').first.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(4000)
    return activity_id


def current_step(page):
    """Return the name of the workflow step that is highlighted.

    :param page: playwright page
    :return: step name, e.g. ``Item Link``
    """
    marker = page.locator('.action-name.cur_step')
    return marker.first.inner_text().strip() if marker.count() else ''


def click_next(page):
    """Click the Next button of the screen that is showing.

    Every step of the activity is in the page at once, so only the visible
    Next belongs to the screen the user is looking at.
    """
    page.get_by_role('button', name=re.compile(r'^\s*Next')).locator(
        'visible=true').first.click()


def advance_to(page, name, timeout=300):
    """Click Next until the activity reaches a named step.

    A step can span several screens -- Item Registration is metadata, then
    index designation, then a comment -- and the step marker only changes on
    the last of them, so reaching the next step means clicking Next as often
    as the screens require.

    :param page: playwright page
    :param name: step name to stop at, e.g. ``Item Link``
    :param timeout: seconds to keep trying
    """
    deadline = time.time() + timeout
    clicked_at = 0
    while time.time() < deadline:
        force_unlock(page)
        if current_step(page) == name:
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)
            return
        button = page.get_by_role(
            'button', name=re.compile(r'^\s*Next')).locator('visible=true')
        if button.count() and time.time() - clicked_at > 8:
            button.first.click()
            clicked_at = time.time()
        page.wait_for_timeout(1500)
    _stuck(page, name)


def wait_for_step(page, name, timeout=180):
    """Wait until the activity has moved on to a named step.

    Saving an item runs long enough that the next screen is still spinning
    when the click returns, and a screenshot taken then shows a spinner.

    :param page: playwright page
    :param name: step name to wait for, e.g. ``Identifier Grant``
    :param timeout: seconds to wait
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        page.wait_for_timeout(1000)
        force_unlock(page)
        if current_step(page) == name:
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)
            return
    _stuck(page, name)


def _stuck(page, name):
    """Fail with what the screen was showing when a step did not arrive."""
    modals = page.locator('.modal:visible')
    detail = modals.first.inner_text() if modals.count() else '(no dialog)'
    evidence = os.path.join(tempfile.gettempdir(), 'weko-stuck.png')
    page.screenshot(path=evidence, full_page=True)
    raise AssertionError(
        'stuck on step "{0}", waiting for "{1}"; showing: {2}; '
        'screen saved to {3}'.format(
            current_step(page), name, detail.replace(chr(10), ' | '),
            evidence))


# -- the flow --------------------------------------------------------------

def test_01_login(page, base_url, credentials):
    """Log in as a system administrator."""
    page.goto('{0}/login/?next=%2F'.format(base_url))
    page.wait_for_load_state('networkidle')
    page.fill('input[name=email]', credentials['email'])
    page.fill('input[name=password]', credentials['password'])
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')
    assert '/login/' not in page.url, 'login failed'

    banner = page.get_by_role('button', name="That's ok")
    if banner.count() and banner.first.is_visible():
        banner.first.click()
        page.wait_for_timeout(500)


def test_02_identifier_settings(page, base_url, shot):
    """Set the Crossref prefix and turn the Crossref grant on."""
    page.goto('{0}/admin/identifier/'.format(base_url))
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    shot(page, '02-identifier-list')

    page.locator("a[href*='/admin/identifier/edit/']").first.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)

    # The prefix box stays read only until the grant is enabled, and the
    # grant is enabled by moving it from Disable to Enable in the dual list.
    if not page.locator('#jalc_crossref_flag').is_checked():
        page.locator('#leftSelect').select_option('jalc_crossref_doi')
        page.locator('#moveRight').click()
        page.wait_for_timeout(500)
    page.fill('#jalc_crossref_doi', CROSSREF_PREFIX)
    shot(page, '03-identifier-edit')

    page.locator("input[type=submit][value='Save']").first.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    shot(page, '04-identifier-saved')

    row = page.locator('table tbody tr').first.inner_text()
    assert CROSSREF_PREFIX in row, row


def test_03_start_activity(page, base_url, shot):
    """Start a new activity on the default full workflow."""
    page.goto('{0}/workflow/activity/new'.format(base_url))
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    shot(page, '05-workflow-list')

    page.locator('#btn-begin-1').click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(6000)

    # Earlier runs may have left activities open, and WEKO names them one at
    # a time, so quit them until it lets a new one start.
    for _ in range(5):
        if '/workflow/activity/detail/' in page.url:
            break
        if not quit_open_activity(page, base_url):
            break
        page.goto('{0}/workflow/activity/new'.format(base_url))
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        page.locator('#btn-begin-1').click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(6000)

    force_unlock(page)
    assert '/workflow/activity/detail/' in page.url, page.url


def test_04_item_metadata(page, shot):
    """Attach a file and fill the metadata Crossref requires.

    A DOI grant is refused without jpcoar:URI, so the item needs a file even
    though Crossref itself does not ask for one.
    """
    page.locator("//input[@type='file']").set_input_files(sample_file())
    page.get_by_role('button', name='Start upload').click()
    page.wait_for_selector(
        '//tr[contains(@class, "sel-file")]//span[@ng-show="f.completed"]',
        timeout=120000)
    page.wait_for_timeout(2000)

    field(page, 'pubdate').fill(PUB_DATE)

    field(page,
          'item_{0}_title0.0.subitem_title'.format(ITEM_TYPE)).fill(TITLE)
    field(page, 'item_{0}_title0.0.subitem_title_language'.format(
        ITEM_TYPE)).select_option('string:en')

    field(page, 'item_{0}_resource_type13.resourcetype'.format(
        ITEM_TYPE)).select_option('string:journal article')

    field(page, 'item_{0}_source_title23.0.subitem_source_title'.format(
        ITEM_TYPE)).fill(JOURNAL_TITLE)
    field(page,
          'item_{0}_source_title23.0.subitem_source_title_language'.format(
              ITEM_TYPE)).select_option('string:en')

    field(page,
          'item_{0}_source_identifier22.0.subitem_source_identifier'.format(
              ITEM_TYPE)).fill(ISSN)
    field(page,
          'item_{0}_source_identifier22.0.'
          'subitem_source_identifier_type'.format(
              ITEM_TYPE)).select_option('string:ISSN')

    # The date picker's visible input carries the bare sub item name.
    field(page, 'subitem_date_issued_datetime').fill(PUB_DATE)
    field(page, 'item_{0}_date11.0.subitem_date_issued_type'.format(
        ITEM_TYPE)).select_option('string:Issued')

    shot(page, '06-item-metadata')
    click_next(page)
    # The index tree of the next screen, not the tree the theme shows anyway.
    page.wait_for_selector(
        '//*[contains(@class, "node-name") and text()="{0}"]'.format(
            INDEX_NAME), timeout=180000)


def test_05_index(page, shot):
    """Put the item in an index and move on.

    The Next button of this step is refused while Designate Index is empty,
    so the checkbox is ticked through the index tree node rather than by
    position.
    """
    page.wait_for_timeout(2000)
    page.locator(
        '//*[contains(@class, "node-name") and text()="{0}"]'
        '/../..//input[@type="checkbox"]'.format(INDEX_NAME)).first.check()
    page.wait_for_timeout(1500)
    assert INDEX_NAME in page.locator('#detail_index, .designate-index').or_(
        page.get_by_text('DESIGNATE INDEX').locator('xpath=../..')
    ).first.inner_text()
    shot(page, '07-index-selected')
    advance_to(page, 'Item Link')


def test_06_item_link(page, shot):
    """Skip the item link step."""
    shot(page, '08-item-link')
    click_next(page)
    wait_for_step(page, 'Identifier Grant')


def test_07_identifier_grant(page, shot):
    """Choose the Crossref DOI grant."""
    shot(page, '09-identifier-grant')
    radio = page.locator("input[type=radio][value='2']").locator(
        'visible=true')
    assert radio.count(), 'Crossref grant not offered'
    radio.first.check()
    page.wait_for_timeout(1000)
    shot(page, '10-identifier-grant-crossref')
    click_next(page)
    wait_for_step(page, 'Approval')


def test_08_approval(page, shot):
    """Approve the activity, which is where the DOI is granted."""
    shot(page, '11-approval')
    page.get_by_role('button', name=re.compile('Approval')).first.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(6000)
    shot(page, '12-approved')


def test_09_granted_identifier(page, shot):
    """Open the registered item from the activity and read its DOI."""
    page.get_by_role('link', name=TITLE).first.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(4000)
    shot(page, '13-granted-identifier')

    body = page.locator('body').inner_text()
    assert CROSSREF_PREFIX in body, 'the granted DOI is not shown'
