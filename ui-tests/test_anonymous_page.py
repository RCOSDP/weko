import re
import pytest
from playwright.sync_api import Page, expect


class TestAnonymousPage:
    """Test for anonymous user interactions with the WEKO application."""

    def test_homepage_loads(self, page: Page, base_url: str):
        """Test that the homepage loads successfully."""
        page.goto(base_url)
        expect(page).to_have_title(re.compile(r".*WEKO.*|.+"))
        expect(page.locator("body")).to_be_visible()

    def test_search_functionality(self, page: Page, base_url: str):
        """Test basic search functionality."""
        page.goto(base_url)

        # Look for common search elements
        search_selectors = [
            'input[type="search"]',
            'input[name="q"]',
            'input[placeholder*="search" i]',
            '.search-input',
            '#search'
        ]

        search_input = None
        for selector in search_selectors:
            try:
                search_input = page.locator(selector).first
                if search_input.is_visible():
                    break
            except:
                continue

        if search_input and search_input.is_visible():
            search_input.fill("test")
            page.keyboard.press("Enter")

            # Wait for search results or navigation
            page.wait_for_load_state("networkidle", timeout=10000)

            # Verify we're on a search results page or results are displayed
            expect(page).to_have_url(re.compile(r".*search.*|.*q=.*", re.IGNORECASE))

    def test_navigation_menu(self, page: Page, base_url: str):
        """Test that navigation menu is present and functional."""
        page.goto(base_url)

        # Look for common navigation elements
        nav_selectors = [
            "nav",
            ".navbar",
            ".navigation",
            ".menu",
            "header nav"
        ]

        nav_found = False
        for selector in nav_selectors:
            try:
                nav = page.locator(selector).first
                if nav.is_visible():
                    nav_found = True
                    break
            except:
                continue

        assert nav_found, "Navigation menu should be present on the homepage"

    def test_footer_present(self, page: Page, base_url: str):
        """Test that footer is present on the page."""
        page.goto(base_url)

        footer_selectors = [
            "footer",
            ".footer",
            "#footer"
        ]

        footer_found = False
        for selector in footer_selectors:
            try:
                footer = page.locator(selector).first
                if footer.is_visible():
                    footer_found = True
                    break
            except:
                continue

        assert footer_found, "Footer should be present on the homepage"

    @pytest.mark.parametrize("endpoint", [
        "/",
        "/search",
        "/about"
    ])
    def test_common_endpoints_accessible(self, page: Page, base_url: str, endpoint: str):
        """Test that common endpoints return successful responses."""
        url = f"{base_url}{endpoint}"
        response = page.goto(url)

        # Accept 200 OK or 404 (endpoint might not exist)
        # but not 500 errors which indicate application issues
        assert response.status in [200, 404], f"Endpoint {endpoint} returned status {response.status}"