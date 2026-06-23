"""TikTok posting helper: tries Business API first, falls back to browser automation.

This module exposes upload_to_tiktok which will attempt a Business API upload if an API key is provided,
otherwise it uses the Playwright automation fallback implemented in poster_tiktok_playwright.py.

CAUTION: Browser automation may violate TikTok's Terms of Service. Use at your own risk.
"""
import os

from typing import Optional

# Business API would be implemented here. For now, we keep the existing placeholder behavior.


def upload_to_tiktok(video_path: str, caption: str, api_key: Optional[str] = None):
    """Upload to TikTok. If api_key is provided implement the Business API upload; otherwise use automation fallback.

    This function returns True on likely-success, False otherwise.
    """
    if api_key:
        # TODO: implement TikTok Business API upload when you have API access and docs for your app
        raise NotImplementedError('TikTok Business API upload not implemented in this prototype. Provide API access and I can implement it.')

    # Use automation fallback
    try:
        from .poster_tiktok_playwright import upload_to_tiktok_playwright
    except Exception as e:
        raise RuntimeError('Playwright fallback not available. Install playwright and run `playwright install`.') from e

    username = os.getenv('TIKTOK_USERNAME')
    password = os.getenv('TIKTOK_PASSWORD')
    return upload_to_tiktok_playwright(video_path, caption, username=username, password=password, headless=True)
