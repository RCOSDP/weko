import pytest
from playwright.sync_api import Page, expect
from utils import login, create_item, change_to_private, delete_item, create_temp_zip_file


class TestImportToGakuninRDMButton:
    """Test Import to GakuNin RDM button."""

    @pytest.fixture
    def test_file_path(self):
        """Path to test file for upload."""
        return create_temp_zip_file()

    def test_import_to_gakunin_rdm_button_enabled(self, page: Page, base_url: str, test_credentials: dict, test_file_path: str):
        """Test that Import to GakuNin RDM button is enabled after creating an item with application/rdm-project format."""
        try:
            login(page, base_url, test_credentials["email"], test_credentials["password"])

            test_title = "Test Item for GakuNin RDM Import"
            create_item(page, test_file_path, test_title, "application/rdm-project")

            # "Import to GakuNin RDM" button should be visible and enabled when the item is published
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).to_be_visible()
            expect(import_button).to_be_enabled()

            change_to_private(page)

            # After changing to private, the button should be visible but disabled
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).to_be_visible()
            expect(import_button).to_be_disabled()

        finally:
            try:
                delete_item(page)
                page.wait_for_load_state("networkidle")
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test item: {cleanup_error}")

    def test_import_to_gakunin_rdm_button_not_visible_for_non_rdm_format(self, page: Page, base_url: str, test_credentials: dict, test_file_path: str):
        """Test that Import to GakuNin RDM button is not visible when format is not application/rdm-project."""
        try:
            login(page, base_url, test_credentials["email"], test_credentials["password"])

            test_title = "Test Item with Non-RDM Format"
            create_item(page, test_file_path, test_title, "application/zip")

            # "Import to GakuNin RDM" button should not be visible for non-RDM format
            import_button = page.locator('button:has-text("Import to GakuNin RDM")')
            expect(import_button).not_to_be_visible()

        finally:
            try:
                delete_item(page)
                page.wait_for_load_state("networkidle")
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up test item: {cleanup_error}")
