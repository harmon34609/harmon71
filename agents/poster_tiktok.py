"""TikTok posting helper: tries Business API first, falls back to browser automation.

Updated to call the Business API helper implemented in poster_tiktok_api.py when an access token
is provided (TIKTOK_ACCESS_TOKEN). If the API-based upload is not available or fails, this will
fall back to the Playwright automation module.

CAUTION: Browser automation may violate TikTok's Terms of Service. Use at your own risk.
"""
import os
from typing import Optional

from .poster_tiktok_playwright import upload_to_tiktok_playwright

try:
    from .poster_tiktok_api import upload_to_tiktok_business, TikTokAPIError
except Exception:
    upload_to_tiktok_business = None
    TikTokAPIError = Exception


def upload_to_tiktok(video_path: str, caption: str, api_key: Optional[str] = None):
    """Upload to TikTok. If api_key / access token is provided, attempt the Business API upload; otherwise use automation fallback.

    Returns True on likely success, False otherwise (for the automation path) or the API response dict on Business API success.
    """
    # Prefer a provided api_key argument, then environment variables
    access_token = api_key or os.getenv('TIKTOK_ACCESS_TOKEN')

    if access_token and upload_to_tiktok_business is not None:
        try:
            print('Attempting TikTok Business API upload...')
            resp = upload_to_tiktok_business(video_path, caption, access_token=access_token)
            print('TikTok Business API upload succeeded (response above).')
            return resp
        except TikTokAPIError as e:
            print('TikTok Business API upload failed:', e)
            print('Falling back to browser automation...')
        except Exception as e:
            print('Unexpected error from Business API upload:', e)
            print('Falling back to browser automation...')

    # Use Playwright automation fallback
    try:
        username = os.getenv('TIKTOK_USERNAME')
        password = os.getenv('TIKTOK_PASSWORD')
        storage_state = os.getenv('TIKTOK_STORAGE_STATE')  # optional path to saved Playwright storage
        return upload_to_tiktok_playwright(video_path, caption, username=username, password=password, storage_state=storage_state, headless=True)
    except Exception as e:
        raise RuntimeError('TikTok upload failed: neither Business API nor Playwright fallback succeeded') from e
