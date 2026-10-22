
import os
import json

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("E2E_BASE_URL", "https://localhost:8443")
USERNAME = os.getenv("APP_USERNAME")
PASSWORD = os.getenv("APP_PASSWORD")

pytestmark = pytest.mark.e2e


def test_ui_displays_redacted_message():
    original_message = (
        "Contact ui-secret@example.com at 172.16.0.8 JWT: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c Card: 4111111111111111"
    )

    expected_message = (
        "Contact [REDACTED_EMAIL] at [REDACTED_IPV4] JWT: [REDACTED_JWT] Card: [REDACTED_CREDIT_CARD]"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            http_credentials={
                "username": USERNAME,
                "password": PASSWORD,
            },
            ignore_https_errors=True,
        )
        page = context.new_page()
        message_id = None

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # Create a message through the API.
            response = page.request.post(
                f"{BASE_URL}/api/messages",
                data=json.dumps({"message": original_message}),
                headers={"Content-Type": "application/json"},
            )

            assert response.status == 201, (
                f"Create failed: {response.status} {response.text()}"
            )

            message_id = response.json()["id"]

            # Reload the page and locate the specific message row.
            page.reload(wait_until="domcontentloaded")

            row = page.locator(
                f'tr[data-message-id="{message_id}"]'
            )

            assert row.count() == 1
            actual_message = row.locator("td").nth(1).inner_text()

            # Validate the complete redacted message.
            assert actual_message == expected_message

            # Verify the original sensitive values are not displayed.
            body = page.locator("body").inner_text()

            assert "ui-secret@example.com" not in body
            assert "172.16.0.8" not in body
            assert (
                "eyJhbGciOiJIUzI1NiJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
                "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            ) not in body
            assert "4111111111111111" not in body

        finally:
            # Remove test data even if an assertion fails.
            if message_id is not None:
                try:
                    page.request.delete(
                        f"{BASE_URL}/api/messages/{message_id}"
                    )
                except Exception:
                    pass

            context.close()
            browser.close()


def test_ui_deleted_message_is_not_displayed():
    original_message = "Temporary message for deletion testing."

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            http_credentials={
                "username": USERNAME,
                "password": PASSWORD,
            },
            ignore_https_errors=True,
        )
        page = context.new_page()
        message_id = None

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # Create the message and store its generated ID.
            response = page.request.post(
                f"{BASE_URL}/api/messages",
                data=json.dumps({"message": original_message}),
                headers={"Content-Type": "application/json"},
            )

            assert response.status == 201, (
                f"Create failed: {response.status} {response.text()}"
            )

            message_id = response.json()["id"]

            page.reload(wait_until="domcontentloaded")

            row_selector = f'tr[data-message-id="{message_id}"]'

            # Verify that the message initially exists in the UI.
            assert page.locator(row_selector).count() == 1
            assert (
                page.locator(row_selector)
                .locator("td")
                .nth(1)
                .inner_text()
                == original_message
            )

            # Delete the message using its generated ID.
            delete_response = page.request.delete(
                f"{BASE_URL}/api/messages/{message_id}"
            )

            assert delete_response.status == 204, (
                f"Delete failed: {delete_response.status} "
                f"{delete_response.text()}"
            )

            # Reload and verify that the row is gone.
            page.reload(wait_until="domcontentloaded")

            assert page.locator(row_selector).count() == 0
            assert original_message not in page.locator(
                "body"
            ).inner_text()

        finally:
            # Cleanup if the test fails before deletion succeeds.
            if message_id is not None:
                try:
                    page.request.delete(
                        f"{BASE_URL}/api/messages/{message_id}"
                    )
                except Exception:
                    pass

            context.close()
            browser.close()
