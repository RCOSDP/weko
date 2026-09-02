"""Fixtures for the Crossref DOI manual capture.

The screenshots in ``works/crossref-doi-manual/images`` are produced by this
run, so the fixtures here are about making a capture reproducible rather than
about asserting behaviour: a fixed viewport, a fixed screenshot directory and
numbered file names, so that re-running the suite replaces the images in place
and the manual never drifts from the application.
"""

import os

import pytest
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.abspath(os.path.join(HERE, os.pardir, 'images'))


@pytest.fixture(scope='session')
def base_url():
    """Return the URL the WEKO instance is published on."""
    return os.getenv('WEKO_BASE_URL', 'https://weko3.example.org:8443')


@pytest.fixture(scope='session')
def host_map():
    """Return the chromium host resolver rule for the WEKO host name.

    WEKO builds absolute URLs from the Host header, so the capture browses
    ``weko3.example.org`` rather than ``localhost`` and the screenshots show
    the host name a real deployment would.  Set ``WEKO_HOST_MAP`` to an empty
    string when DNS already resolves the name.
    """
    return os.getenv('WEKO_HOST_MAP', 'MAP weko3.example.org 127.0.0.1')


@pytest.fixture(scope='session')
def credentials():
    """Return the account the capture logs in with."""
    return {
        'email': os.getenv('WEKO_TEST_EMAIL', 'wekosoftware@nii.ac.jp'),
        'password': os.getenv('WEKO_TEST_PASSWORD', 'uspass123'),
    }


@pytest.fixture(scope='session')
def browser(host_map):
    """Return one browser for the whole capture.

    One browser and one page for every step: WEKO locks an activity to the
    session that opened it, so a flow split across contexts locks itself out.
    """
    args = ['--host-resolver-rules={0}'.format(host_map)] if host_map else []
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(
            headless=os.getenv('WEKO_HEADED', '') == '', args=args)
        yield instance
        instance.close()


@pytest.fixture(scope='session')
def page(browser):
    """Return the page every step of the capture shares."""
    context = browser.new_context(
        ignore_https_errors=True,
        viewport={'width': 1440, 'height': 1000},
        locale='en-US')
    context.set_default_timeout(60000)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope='session')
def shot():
    """Return a function that writes a numbered screenshot.

    :return: ``shot(page, name, full_page=True)``, writing
        ``works/crossref-doi-manual/images/<name>.png``
    """
    if not os.path.isdir(IMAGES):
        os.makedirs(IMAGES)

    def take(page, name, full_page=True, clip=None):
        """Write one screenshot and return its path."""
        path = os.path.join(IMAGES, '{0}.png'.format(name))
        page.wait_for_timeout(500)
        page.screenshot(path=path, full_page=full_page, clip=clip)
        print('screenshot: {0}'.format(path))
        return path

    return take
