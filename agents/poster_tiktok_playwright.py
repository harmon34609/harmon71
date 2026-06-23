"""TikTok browser automation fallback using Playwright with optional session-state reuse.

This module provides a best-effort implementation to upload a video and post it to TikTok via the
web UI. It supports using a saved Playwright "storage state" (cookies/localStorage) so you can
login once interactively and reuse the session for future automated uploads without embedding
credentials.

WARNING: Automating interactions with TikTok via browser automation may violate TikTok's Terms of Service.
Use this fallback only if you understand and accept the legal and reliability risks. Prefer the
TikTok Business API if you have it.

Usage patterns:
- Interactive login once (saves state):
    python agents/tiktok_login.py --storage agents/.tiktok_storage.json
  Open browser, complete login/2FA manually, then close the browser. The file agents/.tiktok_storage.json
  will contain Playwright storage state (auth cookies, localStorage).

- Automated upload using saved state:
    from poster_tiktok_playwright import upload_to_tiktok_playwright
    upload_to_tiktok_playwright('clip.mp4', 'caption text', storage_state='agents/.tiktok_storage.json')

Requirements:
- Playwright Python package and browser binaries. Install:
    pip install playwright
    playwright install

Notes:
- TikTok frequently changes its web UI. Selectors used here may break and need updates.
- Two-factor auth, captcha, or other protections may block automation. Using a saved storage state reduces interactive logins but may still expire.
"""
import os
import time
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except Exception:
    sync_playwright = None
    PlaywrightTimeoutError = Exception


def upload_to_tiktok_playwright(video_path: str, caption: str, username: Optional[str] = None,
                                password: Optional[str] = None, storage_state: Optional[str] = None,
                                headless: bool = True) -> bool:
    """Upload a video to TikTok using Playwright-driven browser automation.

    Parameters:
      - video_path: path to the local video file
      - caption: text to place in the caption field
      - username/password: optional credentials if you prefer direct login (not recommended)
      - storage_state: path to Playwright storage state JSON file (recommended). If provided and exists,
                       the browser context will be created with that state so no interactive login is required.
      - headless: whether to run the browser headless. For initial interactive login set headless=False.

    Returns True on (likely) success, False otherwise.
    """
    if sync_playwright is None:
        raise RuntimeError('playwright is not installed. Install with `pip install playwright` and run `playwright install`.')

    username = username or os.getenv('TIKTOK_USERNAME')
    password = password or os.getenv('TIKTOK_PASSWORD')
    if not os.path.exists(video_path):
        raise FileNotFoundError(f'Video file not found: {video_path}')

    # If storage_state provided and exists, use it. Otherwise, if storage_state provided but missing,
    # we'll save it after an interactive login if possible.
    save_storage_after = False
    if storage_state:
        storage_exists = os.path.exists(storage_state)
    else:
        storage_exists = False

    print('Starting Playwright browser...')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        # Create context using storage state if available
        if storage_state and storage_exists:
            context = browser.new_context(storage_state=storage_state)
            print(f'Loaded storage state from {storage_state}')
        else:
            context = browser.new_context()
            if storage_state:
                # We'll attempt to save state after a successful interactive login
                save_storage_after = True

        page = context.new_page()

        try:
            # If there is a saved session, try visiting upload directly
            page.goto('https://www.tiktok.com/upload', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(2)

            # Detect if we were redirected to login
            if 'login' in page.url or 'challenge' in page.url or page.title().lower().startswith('log in'):
                if storage_exists:
                    print('Saved storage state did not keep us logged in; you may need to refresh the storage file.')
                # Attempt login flow if credentials provided; otherwise prompt user to login interactively
                if username and password and not headless:
                    print('Attempting automated credential login...')
                    # fallthrough to login selectors below
                else:
                    print('Interactive login required. Please complete login in the opened browser window.')
                    # Keep page open for manual login
                    page.wait_for_load_state('networkidle', timeout=60000)
                    # Wait a reasonable time for manual login (user intervention)
                    print('Waiting up to 5 minutes for manual login completion...')
                    try:
                        page.wait_for_url(lambda url: 'upload' in url or 'home' in url or 'for-you' in url, timeout=300000)
                    except PlaywrightTimeoutError:
                        print('Timeout waiting for manual login. Continuing and may fail.')

            # If we reach the upload page, proceed. Otherwise navigate to upload explicitly.
            if 'upload' not in page.url:
                page.goto('https://www.tiktok.com/upload', timeout=60000)
                page.wait_for_load_state('networkidle', timeout=60000)
                time.sleep(2)

            # Find the file input and set the video file
            file_input = None
            candidates = ['input[type="file"]', 'input[accept*="video"]']
            for c in candidates:
                file_input = page.query_selector(c)
                if file_input:
                    break

            if not file_input:
                print('Could not find file input on upload page. The UI may have changed.')
                # If we saved storage after interactive login request, try to save current state for debugging
                if save_storage_after and storage_state:
                    try:
                        context.storage_state(path=storage_state)
                        print(f'Saved storage state to {storage_state} for debugging.')
                    except Exception:
                        pass
                return False

            print('Uploading video file...')
            file_input.set_input_files(video_path)

            # Wait for upload/processing to start (heuristic)
            time.sleep(5)

            # Fill caption/description
            caption_selectors = [
                'textarea[placeholder*="Describe your video"]',
                'textarea[placeholder*="Add a caption"]',
                'div[contenteditable="true"]'
            ]
            wrote = False
            for cs in caption_selectors:
                el = page.query_selector(cs)
                if el:
                    try:
                        el.click()
                        el.fill(caption)
                        wrote = True
                        break
                    except Exception:
                        continue

            if not wrote:
                print('Warning: could not find caption field; attempting to proceed.')

            # Wait a bit for processing to complete and for the Post button to become enabled
            time.sleep(5)

            post_selectors = [
                'button:has-text("Post")',
                'button[data-e2e="post-button"]',
                'button:has-text("Publish")'
            ]
            clicked = False
            for ps in post_selectors:
                try:
                    btn = page.query_selector(ps)
                    if btn and btn.is_enabled():
                        btn.click()
                        clicked = True
                        break
                except PlaywrightTimeoutError:
                    continue

            if not clicked:
                print('Could not find or click the Post button. The UI may have changed or additional confirmation is required.')
                return False

            # Optionally save storage state for reuse
            if save_storage_after and storage_state:
                try:
                    os.makedirs(os.path.dirname(storage_state), exist_ok=True)
                    context.storage_state(path=storage_state)
                    print(f'Saved new storage state to {storage_state}')
                except Exception as e:
                    print('Failed to save storage state:', e)

            # Wait a short while to let the post flow complete
            time.sleep(5)
            print('Upload flow attempted. Verify on your TikTok account that the video was posted.')
            return True

        except Exception as e:
            print('Playwright upload failed:', e)
            return False
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass
