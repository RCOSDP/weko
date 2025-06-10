import os
import tempfile
import re
import time
import zipfile
from playwright.sync_api import Page, expect


def login(page: Page, base_url: str, email: str, password: str, timeout: int=30000) -> None:
    """
    Login to WEKO system
    """
    page.goto(base_url, timeout=timeout)
    ensure_language(page, "en", timeout=timeout)
    page.get_by_role("link", name=" Log in").click()
    page.get_by_placeholder("Email Address").click()
    page.get_by_placeholder("Email Address").fill(email)
    page.get_by_placeholder("Password").click()
    page.get_by_placeholder("Password").fill(password)
    page.get_by_role("button", name=" Log In").click()
    page.wait_for_load_state("networkidle")


def ensure_language(page: Page, language: str, timeout: int=30000) -> None:
    """
    Ensure the displayed language is set to the specified language
    """
    # Try to find language selector by multiple possible labels
    language_selector = None
    possible_labels = ["Language:", "言語:"]
    for label in possible_labels:
        try:
            language_selector = page.get_by_label(label)
            if language_selector.is_visible():
                break
        except:
            continue
    if language_selector is None:
        return
    language_selector.select_option(language)
    page.wait_for_load_state("networkidle", timeout=timeout)


def ensure_index_open_access(page: Page, base_url: str, index_name: str, visible: bool, timeout: int=30000) -> None:
    """
    Ensure index open access setting in WEKO system
    """
    # Navigate to Administration
    page.goto(f"{base_url.rstrip('/')}/admin/indexedit/", timeout=timeout)
    page.wait_for_load_state("networkidle")

    # Find and click on the index (assuming we're working with a default index)
    page.get_by_text(index_name).click()
    time.sleep(5)  # Wait for the page to load

    # Set the open access checkbox based on the parameter
    open_access_checkbox = page.locator("#rss_display").first

    # Check current state and click if needed
    is_checked = open_access_checkbox.is_checked()
    if visible and not is_checked:
        open_access_checkbox.click()
    elif not visible and is_checked:
        open_access_checkbox.click()

    time.sleep(2)  # Wait for the checkbox state to change

    # Prepare dialog handler before clicking Send
    dialog_handled = False
    dialog_message = ""

    def handle_dialog(dialog):
        nonlocal dialog_handled, dialog_message
        dialog_message = dialog.message
        dialog.accept()
        dialog_handled = True

    page.on("dialog", handle_dialog)

    # Save the changes
    page.get_by_role("button", name="Send").click()

    # Wait for alert to appear and be handled with timeout
    start_time = time.time()
    timeout_ms = 10000  # 10 seconds timeout

    while not dialog_handled:
        if (time.time() - start_time) * 1000 > timeout_ms:
            break
        page.wait_for_timeout(100)

    # Verify the dialog message
    if dialog_handled:
        assert "Index is updated successfully." in dialog_message, f"Expected 'Index is updated successfully.' in dialog message, got: {dialog_message}"
    else:
        raise TimeoutError(f"Dialog did not appear within {timeout_ms}ms")

    # Remove dialog handler
    page.remove_listener("dialog", handle_dialog)

    page.wait_for_load_state("networkidle")


def create_item(page: Page, index_name: str, file_path: str, title: str, format_type: str = "application/zip") -> None:
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
    checkbox = page.locator(f'//*[contains(@class, "node-name") and text()="{index_name}"]/../..//input[@type="checkbox"]')
    checkbox.check()
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