import pytest
import requests
import hashlib
from playwright.sync_api import Page, expect
from urllib.parse import urlparse, parse_qs
from utils import (
    login, create_item, change_to_private, delete_item, create_temp_zip_file, ensure_index_open_access,
    ensure_language
)


class TestImportToGakuninRDMButton:
    """Test Import to GakuNin RDM button."""

    @pytest.fixture(autouse=True)
    def setup_index_access(self, page: Page, base_url: str, test_credentials: dict, index_name: str):
        """Setup fixture to ensure index is public at start and private at end."""
        # Login and set index to public before each test
        login(page, base_url, test_credentials["email"], test_credentials["password"], timeout=60000)
        ensure_index_open_access(page, base_url, index_name, True)

        yield

        # Set index to private after each test
        try:
            ensure_index_open_access(page, base_url, index_name, False)
        except Exception as cleanup_error:
            print(f"Warning: Failed to clean up index access: {cleanup_error}")

    @pytest.fixture
    def index_name(self):
        """Index name to use for testing."""
        return "Sample Index"

    @pytest.fixture
    def test_file_path(self):
        """Path to test file for upload."""
        return create_temp_zip_file()

    @pytest.mark.xfail(
        reason=(
            "weko_index_tree bug, not a test one: check_groups() in "
            "weko_index_tree.utils computes "
            "any(r in user_group_list for r in index_group_list), so it "
            "returns False whenever the index configures no browsing groups - "
            "any() over an empty sequence is False. check_index_permissions "
            "therefore denies every non-admin, anonymous or logged in, on any "
            "index without groups, and WEKO answers the anonymous file "
            "request with a redirect to /login instead of the file. v2.0.4's "
            "check_roles started from is_can = True and had no such gate. The "
            "same defect is why invenio-records-rest's test_default_permissions "
            "now answers 401. GakuNin RDM fetches the file anonymously, so this "
            "test cannot pass until weko_index_tree.utils is fixed. See "
            "docs/v2.1.0-test-reconciliation.md."
        ),
    )
    def test_import_to_gakunin_rdm_button_enabled(self, page: Page, base_url: str, index_name: str, test_file_path: str, gakunin_rdm_url: str):
        """Test that Import to GakuNin RDM button is enabled after creating an item with application/rdm-project format."""
        try:
            page.goto(base_url)
            test_title = "Test Item for GakuNin RDM Import"
            create_item(page, index_name, test_file_path, test_title, "application/rdm-project")

            # "Import to GakuNin RDM" button should be visible and enabled when the item is published
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).to_be_visible(timeout=30000)
            expect(import_button).to_be_enabled()

            # Check that the parent anchor tag has the correct href attribute with GakuNin RDM URL
            import_link = page.locator('a:has(button:has-text("Import to GakuNin RDM"))')
            href_attr = import_link.get_attribute("href")
            assert href_attr is not None, "Import button parent link should have href attribute"

            # Validate URL structure using urlparse
            parsed_url = urlparse(href_attr)

            # Check scheme + host matches the configured GakuNin RDM
            expected_base = gakunin_rdm_url
            actual_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
            assert actual_base == expected_base, f"URL base should be {expected_base}, got {actual_base}"

            # Get query parameters
            query_params = parse_qs(parsed_url.query)
            assert "url" in query_params, "URL should contain 'url' parameter"

            # Validate that url parameter starts with base_url
            url_param = query_params["url"][0]
            assert url_param.startswith(base_url), f"URL parameter should start with {base_url}, got {url_param}"

            # Validate that the URL is accessible and contains equivalent content to test_file_path
            # Get the content from the URL parameter
            response = requests.get(url_param, timeout=10, verify=False)
            assert response.status_code == 200, f"URL should be accessible, got status {response.status_code}"

            # Check MIME type
            content_type = response.headers.get('content-type', '').lower()
            if test_file_path.endswith('.zip'):
                expected_mime_types = ['application/zip', 'application/x-zip-compressed', 'application/octet-stream']
                # requests carries no browser session, so this is an anonymous
                # fetch - which is the point: GakuNin RDM pulls the file this
                # way. When WEKO answers with a page instead of the file the
                # status is still 200, so report where the request ended up and
                # what came back, otherwise the content type alone says nothing
                # about why.
                assert any(mime_type in content_type for mime_type in expected_mime_types), (
                    f"Response content-type should be one of {expected_mime_types}, "
                    f"got: {content_type}\n"
                    f"requested: {url_param}\n"
                    f"final url: {response.url}\n"
                    f"redirects: {[r.headers.get('location') for r in response.history]}\n"
                    f"body[:400]: {response.text[:400]!r}"
                )
            else:
                # For other file types, check for octet-stream as fallback
                assert 'application/octet-stream' in content_type or content_type != '', \
                    f"Response should have valid content-type, got: {content_type}"

            # Read original test file content and calculate MD5 hash
            with open(test_file_path, 'rb') as f:
                original_content = f.read()
            original_md5 = hashlib.md5(original_content).hexdigest()

            # Calculate MD5 hash of downloaded content
            downloaded_md5 = hashlib.md5(response.content).hexdigest()

            # Compare MD5 hashes to ensure content equivalence
            assert original_md5 == downloaded_md5, f"Downloaded content MD5 ({downloaded_md5}) should match original file MD5 ({original_md5})"

            # Change language to Japanese and verify button text changes
            ensure_language(page, "ja")
            import_button_ja = page.locator('button:has-text("GakuNin RDMにインポート")')
            expect(import_button_ja).to_be_visible(timeout=30000)
            expect(import_button_ja).to_be_enabled()

            # Change language back to English
            ensure_language(page, "en")
            import_button_en = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button_en).to_be_visible(timeout=30000)
            expect(import_button_en).to_be_enabled()

            change_to_private(page)

            # After changing to private, the button should be visible but disabled
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).to_be_visible()
            expect(import_button).to_be_disabled()

            # Check that the URL cannot be accessed when the item is private
            response = requests.get(url_param, timeout=10, verify=False)
            assert response.status_code == 200, f"URL should be accessible, got status {response.status_code}"
            content_type = response.headers.get('content-type', '').lower()
            assert 'text/html' in content_type, f"Response content-type should be text/html, got: {content_type}"

        finally:
            try:
                delete_item(page)
                page.wait_for_load_state("networkidle")
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test item: {cleanup_error}")

    def test_import_to_gakunin_rdm_button_not_visible_for_non_rdm_format(self, page: Page, base_url: str, index_name: str, test_file_path: str):
        """Test that Import to GakuNin RDM button is not visible when format is not application/rdm-project."""
        try:
            page.goto(base_url)
            test_title = "Test Item with Non-RDM Format"
            create_item(page, index_name, test_file_path, test_title, "application/zip")

            # "Import to GakuNin RDM" button should not be visible for non-RDM format
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).not_to_be_visible()

        finally:
            try:
                delete_item(page)
                page.wait_for_load_state("networkidle")
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test item: {cleanup_error}")
