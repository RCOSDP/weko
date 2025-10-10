import pytest
import os
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the WEKO application."""
    return os.getenv("WEKO_BASE_URL", "https://weko3.example.org")


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments for testing."""
    return {
        "ignore_https_errors": True,
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": "test-results/videos/",
        "record_video_size": {"width": 1280, "height": 720}
    }


@pytest.fixture(scope="session")
def playwright():
    """Playwright instance for the test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright):
    """Browser instance for the test session."""
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def page(browser, browser_context_args, base_url):
    """Page instance for each test."""
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def test_credentials():
    """Test credentials for WEKO system."""
    return {
        "email": os.getenv("WEKO_TEST_EMAIL", "test@weko3.example.org"),
        "password": os.getenv("WEKO_TEST_PASSWORD", "testpassword")
    }
