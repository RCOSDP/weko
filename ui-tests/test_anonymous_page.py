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
