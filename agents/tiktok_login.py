"""Interactive helper to create and save a Playwright storage state for TikTok.

Run this script to open a browser, log in interactively (complete 2FA if needed), and save the storage
state (cookies/localStorage) to the provided JSON file. Later runs of the automation can reuse that file
and avoid password-based logins.

Usage:
  python agents/tiktok_login.py --storage agents/.tiktok_storage.json --headless false

Requirements:
  pip install playwright
  playwright install
"""
import argparse
import os
import time

try:
    from playwright.sync_api import sync_playwright
except Exception:
    print('playwright is required. Install with `pip install playwright` and run `playwright install`.')
    raise


def main():
    parser = argparse.ArgumentParser(description='Interactive TikTok login helper to save Playwright storage state')
    parser.add_argument('--storage', default='agents/.tiktok_storage.json', help='Path to save storage state JSON')
    parser.add_argument('--headless', action='store_true', help='Run headless (not recommended for interactive login)')
    args = parser.parse_args()

    storage_path = args.storage
    headless = args.headless

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        print('Opening TikTok login page. Please complete login and any 2FA/captcha in the opened browser.')
        page.goto('https://www.tiktok.com/login')

        try:
            # Wait for user to complete login. We'll wait until the URL contains 'upload' or the user closes.
            print('Waiting up to 10 minutes for manual login...')
            page.wait_for_url(lambda url: 'upload' in url or 'for-you' in url or 'home' in url, timeout=600000)
            print('Detected login/redirect. Saving storage state...')
        except Exception:
            print('Timeout or unexpected navigation; attempting to save storage state anyway.')

        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        try:
            context.storage_state(path=storage_path)
            print(f'Storage state written to {storage_path}')
        except Exception as e:
            print('Failed to save storage state:', e)

        try:
            context.close()
            browser.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
