"""TikTok browser automation fallback using Playwright.

WARNING: Automating interactions with TikTok via browser automation may violate TikTok's Terms of Service.
Use this fallback only if you understand and accept the legal and reliability risks. Prefer the
TikTok Business API if you have it.

This module provides a best-effort implementation to upload a video and post it to TikTok via the
web UI. It requires the Playwright Python package and browser binaries (run `playwright install`).

Environment variables:
- TIKTOK_USERNAME - your TikTok username or email
- TIKTOK_PASSWORD - your TikTok password

Notes:
- TikTok frequently changes its web UI. Selectors used here may break and need updates.
- Two-factor auth, captcha, or other protections may block automation. You may need to login
  interactively first or use a session cookie.
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
                                password: Optional[str] = None, headless: bool = True) -> bool:
    """Upload a video to TikTok using Playwright-driven browser automation.

    Returns True on (likely) success, False otherwise.
    """
    if sync_playwright is None:
        raise RuntimeError('playwright is not installed. Install with `pip install playwright` and run `playwright install`.')

    username = username or os.getenv('TIKTOK_USERNAME')
    password = password or os.getenv('TIKTOK_PASSWORD')
    if not username or not password:
        raise ValueError('TIKTOK_USERNAME and TIKTOK_PASSWORD must be set in the environment to use the automation fallback')

    if not os.path.exists(video_path):
        raise FileNotFoundError(f'Video file not found: {video_path}')

    print('Starting Playwright browser...')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Go to login page
            page.goto('https://www.tiktok.com/login', timeout=60000)
            time.sleep(2)

            # TikTok may present multiple login options. Try locating the username/email input.
            # If TikTok offers a QR or third-party login, the below might need adjustment.
            try:
                # Click "Use phone / email / username" if present
                sel_switch = 'text="Use phone / email / username"'
                if page.query_selector(sel_switch):
                    page.click(sel_switch)
                    time.sleep(1)
            except PlaywrightTimeoutError:
                pass

            # Attempt to fill username/email and password fields
            # There are several possible selectors; we try a few common ones.
            username_selectors = [
                'input[name="username"]',
                'input[type="text"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Username"]'
            ]
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="Password"]'
            ]

            filled = False
            for us in username_selectors:
                el = page.query_selector(us)
                if el:
                    el.fill(username)
                    filled = True
                    break
            if not filled:
                print('Warning: could not find username input selector; continuing and hoping for SSO or cookie-based login.')

            filled = False
            for ps in password_selectors:
                el = page.query_selector(ps)
                if el:
                    el.fill(password)
                    filled = True
                    break
            if not filled:
                print('Warning: could not find password input selector; continuing.')

            # Try clicking login/submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Login")'
            ]
            for ss in submit_selectors:
                try:
                    btn = page.query_selector(ss)
                    if btn:
                        btn.click()
                        break
                except PlaywrightTimeoutError:
                    continue

            # Give time to login (and potentially handle 2FA manually)
            print('Waiting for login to complete (if 2FA/captcha appears, handle it manually in the opened browser)')
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(3)

            # Navigate to the upload page
            page.goto('https://www.tiktok.com/upload', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(2)

            # Find the file input and set the video file
            file_input = None
            # Common selector for file inputs
            candidates = ['input[type="file"]', 'input[accept*="video"]']
            for c in candidates:
                file_input = page.query_selector(c)
                if file_input:
                    break

            if not file_input:
                print('Could not find file input on upload page. The UI may have changed.')
                return False

            print('Uploading video file...')
            file_input.set_input_files(video_path)

            # Wait for upload/processing to start (heuristic)
            time.sleep(5)

            # Fill caption/description
            # Try common caption textarea selectors
            caption_selectors = [
                'textarea[placeholder*="Describe your video"]',
                'textarea[placeholder*="Add a caption"]',
                'div[contenteditable="true"]'
            ]
            wrote = False
            for cs in caption_selectors:
                el = page.query_selector(cs)
                if el:
                    el.click()
                    el.fill(caption)
                    wrote = True
                    break

            if not wrote:
                print('Warning: could not find caption field; attempting to proceed.')

            # Wait a bit for processing to complete and for the Post button to become enabled
            time.sleep(5)

            # Click Post button (selector may vary)
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
