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

    # The result is reported as an in-page Bootstrap alert, not a browser
    # dialog. weko_index_tree's Angular component renders <div id="alerts">
    # and appends to it:
    #
    #     addAlert = function (msg, type) {
    #       if (type === undefined) type = "danger";
    #       $("#alerts").append('<div class="alert alert-' + type + '" id="">'
    #         + '<button type="button" class="close" data-dismiss="alert">'
    #         + '&times;</button>' + msg + '</div>');
    #     }
    #
    # A successful update passes type="success"; every error path falls back to
    # the default "danger". page.on("dialog") only fires for alert(), confirm(),
    # prompt() and beforeunload, so waiting on it here always timed out - the
    # application never calls any of them.
    #
    # This helper runs twice per test (setup and teardown) and #alerts is only
    # ever appended to, so clear it first to be sure we read the new alert.
    page.evaluate(
        "() => { const el = document.querySelector('#alerts');"
        " if (el) el.innerHTML = ''; }"
    )

    # Save the changes
    page.get_by_role("button", name="Send").click()

    expect(page.locator("#alerts .alert").first).to_be_visible(timeout=timeout)

    # Surface the server's own message rather than a bare assertion failure.
    errors = page.locator("#alerts .alert-danger")
    if errors.count() > 0:
        raise AssertionError(
            "Index update failed: "
            + " / ".join(
                errors.nth(i).inner_text().strip().lstrip("×").strip()
                for i in range(errors.count())
            )
        )

    success = page.locator("#alerts .alert-success").first
    expect(success).to_be_visible(timeout=timeout)
    message = success.inner_text().strip().lstrip("×").strip()
    assert "Index is updated successfully." in message, (
        f"Expected 'Index is updated successfully.' in the alert, got: {message!r}"
    )

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

    # Expand the file metadata section.
    #
    # The section to open is the item type's "File" field (key
    # item_30002_file35), which holds Format, Preview, Access and so on.
    # "File Information" is a different section: it is the item type's
    # system_file, and its render option carries "hidden": true, so it is
    # never shown on the registration form.
    #
    # invenio_deposit's decorators render each section as
    #     <div class="panel-heading">
    #       <a ng-click="collapsed = !collapsed" class="panel-toggle">
    #         {{ form.title }} ...
    # The anchor has no href, so it carries no ARIA link role and
    # get_by_role("link", ...) does not match it. Scope to the heading and
    # match the title exactly instead - a substring match would also hit
    # "File Information".
    #
    # "File" is an array field, and that produces two nested panels with the
    # same title: the array decorator draws one for the array itself, then
    # renders every element through <sf-decorator form="copyWithIndex($index)">,
    # which carries the same title. Both start collapsed
    # (ng-init="collapsed = form.required !== true", and File is Optional), so
    # both have to be opened before Format is reachable. Click them in document
    # order - the array panel comes first, and the element panel only becomes
    # clickable once the array panel is open.
    file_headings = page.locator(".panel-heading").get_by_text("File", exact=True)
    expect(file_headings.first).to_be_visible(timeout=30000)
    for i in range(file_headings.count()):
        heading = file_headings.nth(i)
        expect(heading).to_be_visible(timeout=30000)
        heading.click()

    format_field = page.get_by_label("Format", exact=True)
    expect(format_field).to_be_visible(timeout=30000)
    format_field.click()
    format_field.fill(format_type)
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