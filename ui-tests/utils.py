import os
import tempfile
import re
import zipfile
from playwright.sync_api import Page, expect


def login(page: Page, base_url: str, email: str, password: str) -> None:
    """
    Login to WEKO system
    """
    page.goto(base_url)
    page.get_by_role("link", name=" Log in").click()
    page.get_by_placeholder("Email Address").click()
    page.get_by_placeholder("Email Address").fill(email)
    page.get_by_placeholder("Password").click()
    page.get_by_placeholder("Password").fill(password)
    page.get_by_role("button", name=" Log In").click()
    page.wait_for_load_state("networkidle")


def create_item(page: Page, file_path: str, title: str, format_type: str = "application/zip") -> None:
    """
    Create an item in WEKO system
    """
    page.get_by_role("link", name="Workflow").click()
    page.get_by_role("button", name="+   New Activity").click()
    page.locator("#btn-begin-1").click()
    page.locator("//input[@type='file']").set_input_files(file_path)
    page.get_by_role("button", name="Start upload").click()
    expect(page.locator('//tr[contains(@class, "sel-file")]//span[@ng-show="f.completed"]')).to_be_visible(timeout=30000)

    page.get_by_role("textbox", name="Title*").click()
    page.get_by_role("textbox", name="Title*").fill(title)

    page.get_by_text("File Information").click()
    page.get_by_label("Format", exact=True).click()
    page.get_by_label("Format", exact=True).fill(format_type)
    page.locator("label").filter(has_text="Preview").click()
    page.locator("select[name=\"item_30002_title0\\.0\\.subitem_title_language\"]").select_option("string:ja")
    page.locator("select[name=\"item_30002_resource_type13\\.resourcetype\"]").select_option("string:conference paper")
    page.get_by_role("button", name="Next  ").click()
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Next ").click()
    page.get_by_role("button", name="Next ").click()
    page.get_by_role("button", name="Next ").click()
    page.get_by_role("button", name="Next ").click()
    page.get_by_role("button", name="Approval").click()
    page.get_by_role("button", name="Access").click()


def change_to_private(page: Page) -> None:
    """
    Change item to private in WEKO system
    """
    page.get_by_role("button", name="Change to Private").click()
    expect(page.get_by_text("Change to Public")).to_be_visible()


def delete_item(page: Page) -> None:
    """
    Delete an item in WEKO system
    """
    page.get_by_text("Delete", exact=True).click()
    page.get_by_role("button", name="OK", exact=True).click()
    page.wait_for_url(re.compile(r".*search.*", re.IGNORECASE))

    page.wait_for_load_state("networkidle")

    page.wait_for_timeout(2000)  # Wait for any UI updates


def create_temp_zip_file() -> str:
    """
    Create a temporary ZIP file for testing
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create a temporary file to put in the zip
    temp_file_path = os.path.join(temp_dir, "test_file.txt")
    with open(temp_file_path, "w") as f:
        f.write("This is a test file for UI testing.")

    # Create the zip file
    zip_path = os.path.join(temp_dir, "test_upload.zip")
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.write(temp_file_path, "test_file.txt")

    # Clean up the temporary text file
    os.remove(temp_file_path)

    return zip_path