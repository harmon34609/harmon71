"""TikTok Business API upload scaffold.

This module implements a best-effort, generic scaffold for uploading videos via the TikTok Business
API / Open API. The exact endpoints and parameter names differ by API version and TikTok app,
so this implementation focuses on a clear, testable structure you can adapt for your app.

Environment variables expected (one of the access methods below):
- TIKTOK_ACCESS_TOKEN: If you have an OAuth access token for the Business/OpenAPI, set it here.
- TIKTOK_API_BASE: Optional base URL for the TikTok Business/Open API (defaults to a common base).

Typical flow:
1) Upload video binary using a 'video/upload' or similar endpoint (multipart or resumable).
2) Create a media object / video resource referencing the uploaded file.
3) Create a post referencing the media id and caption.

This module provides helper functions you can adapt to the exact API your TikTok app uses. If you
provide real credentials and the exact API endpoints, I will finalize the concrete implementation.

Note: If you do not have Business API access, the higher-level poster will fall back to browser
automation (Playwright) which is provided in poster_tiktok_playwright.py.
"""
import os
import requests
from typing import Optional


DEFAULT_API_BASE = os.getenv('TIKTOK_API_BASE', 'https://business-api.tiktok.com/open_api/v1.2')


class TikTokAPIError(Exception):
    pass


def upload_video_multipart(video_path: str, access_token: str, api_base: Optional[str] = None) -> str:
    """Upload a video file via a generic multipart endpoint.

    Returns a video_id/media_id string on success. This is a scaffold — replace the endpoint path with
    the exact one your TikTok Business App expects.
    """
    api_base = api_base or DEFAULT_API_BASE
    endpoint = f"{api_base}/video/upload/"

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    with open(video_path, 'rb') as fh:
        files = {
            'video': ('video.mp4', fh, 'video/mp4')
        }
        # Additional params might be required by the API: app_id, open_id, etc.
        params = {}
        resp = requests.post(endpoint, headers=headers, files=files, data=params, timeout=120)

    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'Upload failed (status {resp.status_code}): {resp.text}')

    data = resp.json()
    # The actual response shape varies. Try common keys, otherwise return the whole payload stringified.
    video_id = data.get('data', {}).get('video_id') or data.get('data', {}).get('media_id') or data.get('video_id')
    if not video_id:
        # As a fallback try to return an id-like field or raise
        # For now, return the JSON string so the caller can inspect it
        raise TikTokAPIError(f'Upload succeeded but could not extract video id: {data}')

    return video_id


def create_post_from_media(media_id: str, caption: str, access_token: str, api_base: Optional[str] = None) -> dict:
    """Create a post using a previously uploaded media resource.

    Returns the post creation response as a dict. Replace endpoint/params with your app's spec.
    """
    api_base = api_base or DEFAULT_API_BASE
    endpoint = f"{api_base}/post/create/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'media_id': media_id,
        'text': caption,
        # platform/app-specific params may be needed here
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'Create post failed (status {resp.status_code}): {resp.text}')
    return resp.json()


def upload_to_tiktok_business(video_path: str, caption: str, access_token: Optional[str] = None,
                              api_base: Optional[str] = None) -> dict:
    """High-level helper: upload video and create a post via TikTok Business API.

    This is a best-effort scaffold. You must provide a valid access_token obtained from TikTok Business/OpenAPI.

    Returns the API response for post creation on success.
    """
    access_token = access_token or os.getenv('TIKTOK_ACCESS_TOKEN')
    if not access_token:
        raise TikTokAPIError('No TIKTOK_ACCESS_TOKEN provided — cannot use Business API path')

    api_base = api_base or os.getenv('TIKTOK_API_BASE') or DEFAULT_API_BASE

    # 1) Upload video
    media_id = upload_video_multipart(video_path, access_token, api_base=api_base)

    # 2) Create a post referencing the media
    post_resp = create_post_from_media(media_id, caption, access_token, api_base=api_base)

    return post_resp
