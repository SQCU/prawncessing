import pytest
from playwright.sync_api import Page, expect

def test_visualizer_integration(page: Page):
    page.goto("http://localhost:5000")
    expect(page).to_have_title("CORS Debug Visualizer")
