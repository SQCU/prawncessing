
import pytest
from playwright.sync_api import Page, expect

def test_proxy_server_is_running(page: Page):
    page.goto("http://localhost:8000")
    expect(page).to_have_title("Functional Processor")
