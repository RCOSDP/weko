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

    def test_import_to_gakunin_rdm_button_enabled(self, page: Page, base_url: str, index_name: str, test_file_path: str):
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

            # Check scheme + host is https://rdm.nii.ac.jp
            expected_base = "https://rdm.nii.ac.jp"
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
                assert any(mime_type in content_type for mime_type in expected_mime_types), \
                    f"Response content-type should be one of {expected_mime_types}, got: {content_type}"
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
