"""Resumable TikTok Business API uploader scaffold.

This module implements a configurable, best-effort resumable upload flow that can be adapted to a
variety of TikTok Business/Open API implementations. Because TikTok's exact API endpoints vary by
app and API version, this implementation is intentionally generic and driven by environment
variables that you must set to match your app's API spec.

Environment variables (one of the two flows below must be configured):

Simple multipart flow (if your API supports a single multipart upload):
- TIKTOK_API_MULTIPART_UPLOAD_URL - full URL to POST a multipart upload (video binary)
- TIKTOK_ACCESS_TOKEN - Bearer token for authorization (if required)

Resumable/chunked flow (recommended for large videos):
- TIKTOK_API_INIT_UPLOAD_URL - POST endpoint that initializes a resumable upload and returns an upload_id or upload_urls
- TIKTOK_API_UPLOAD_CHUNK_URL - templated URL or endpoint to upload a chunk; if templated it should contain '{upload_id}' and optionally '{chunk_index}'
- TIKTOK_API_FINALIZE_UPLOAD_URL - POST endpoint to finalize the upload and obtain a media_id
- TIKTOK_CREATE_POST_URL - POST endpoint to create a post from a media_id
- TIKTOK_ACCESS_TOKEN - Bearer token for authorization (if required)

How it works (resumable flow):
1) Call init endpoint to receive an upload_id or upload URLs.
2) Upload the video in chunks to the provided chunk URLs (or to a templated chunk endpoint).
3) Finalize the upload to obtain media_id.
4) Create a post referencing media_id and caption.

This module provides robust retrying and clear, actionable error messages to help you map the
scaffold to your actual TikTok Business API implementation.
"""
import os
import math
import requests
from typing import Optional


class TikTokAPIError(Exception):
    pass


def _auth_headers(access_token: Optional[str]) -> dict:
    headers = {}
    token = access_token or os.getenv('TIKTOK_ACCESS_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def upload_video_multipart(video_path: str, multipart_url: Optional[str] = None, access_token: Optional[str] = None) -> str:
    """Upload a video via a single multipart POST.

    Returns a media_id (string) on success. This function is suitable for small videos when the
    API supports a single-request multipart upload.
    """
    multipart_url = multipart_url or os.getenv('TIKTOK_API_MULTIPART_UPLOAD_URL')
    if not multipart_url:
        raise TikTokAPIError('No multipart upload URL configured (TIKTOK_API_MULTIPART_UPLOAD_URL)')

    headers = _auth_headers(access_token)

    with open(video_path, 'rb') as fh:
        files = {'video': ('video.mp4', fh, 'video/mp4')}
        resp = requests.post(multipart_url, headers=headers, files=files, timeout=180)

    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'multipart upload failed: {resp.status_code} {resp.text}')

    data = resp.json()
    media_id = _extract_media_id(data)
    if not media_id:
        raise TikTokAPIError(f'Upload succeeded but could not extract media id from response: {data}')
    return media_id


def upload_video_resumable(video_path: str, init_url: Optional[str] = None, chunk_url_template: Optional[str] = None,
                           finalize_url: Optional[str] = None, access_token: Optional[str] = None,
                           chunk_size: int = 8 * 1024 * 1024) -> str:
    """Resumable upload using an init/upload-chunk/finalize pattern.

    - init_url: endpoint to initialize the upload. Expected to return JSON with an upload_id and optionally chunk URLs.
    - chunk_url_template: templated endpoint to upload chunks (should contain '{upload_id}' and optionally '{chunk_index}').
    - finalize_url: endpoint to finalize the upload and return a media_id.

    Returns media_id on success.
    """
    init_url = init_url or os.getenv('TIKTOK_API_INIT_UPLOAD_URL')
    chunk_url_template = chunk_url_template or os.getenv('TIKTOK_API_UPLOAD_CHUNK_URL')
    finalize_url = finalize_url or os.getenv('TIKTOK_API_FINALIZE_UPLOAD_URL')

    if not init_url or not chunk_url_template or not finalize_url:
        raise TikTokAPIError('Resumable upload requires TIKTOK_API_INIT_UPLOAD_URL, TIKTOK_API_UPLOAD_CHUNK_URL, and TIKTOK_API_FINALIZE_UPLOAD_URL')

    headers = _auth_headers(access_token)

    # 1) Initialize upload
    resp = requests.post(init_url, headers=headers, json={}, timeout=60)
    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'Init upload failed: {resp.status_code} {resp.text}')

    init_data = resp.json()
    # Extract upload_id or upload URLs
    upload_id = init_data.get('upload_id') or init_data.get('uploadId') or init_data.get('id')
    upload_urls = init_data.get('upload_urls') or init_data.get('chunk_urls') or None

    if not upload_id and not upload_urls:
        raise TikTokAPIError(f'Init response did not contain upload id or upload URLs: {init_data}')

    file_size = os.path.getsize(video_path)
    total_chunks = math.ceil(file_size / chunk_size)

    # 2) Upload chunks
    with open(video_path, 'rb') as fh:
        for chunk_index in range(total_chunks):
            start = chunk_index * chunk_size
            fh.seek(start)
            chunk_data = fh.read(chunk_size)

            # Determine chunk upload URL
            if upload_urls and len(upload_urls) > chunk_index:
                url = upload_urls[chunk_index]
            else:
                # Fill template
                url = chunk_url_template.format(upload_id=upload_id, chunk_index=chunk_index)

            # Attempt to PUT the chunk (many resumable APIs accept PUT). If the API expects POST, adjust accordingly.
            success = False
            attempts = 0
            while not success and attempts < 3:
                attempts += 1
                try:
                    chunk_headers = headers.copy()
                    # Some APIs require Content-Range; include a generic header to help
                    end = min(start + chunk_size, file_size) - 1
                    chunk_headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                    resp = requests.put(url, headers=chunk_headers, data=chunk_data, timeout=120)
                    if resp.status_code in (200, 201, 204):
                        success = True
                        break
                    else:
                        # Retry for server errors
                        if 500 <= resp.status_code < 600:
                            continue
                        else:
                            raise TikTokAPIError(f'Chunk upload failed (status {resp.status_code}): {resp.text}')
                except requests.RequestException as e:
                    if attempts >= 3:
                        raise TikTokAPIError(f'Chunk upload failed after retries: {e}')

    # 3) Finalize upload
    finalize_headers = headers.copy()
    payload = {'upload_id': upload_id} if upload_id else init_data
    resp = requests.post(finalize_url, headers=finalize_headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'Finalize upload failed: {resp.status_code} {resp.text}')

    finalize_data = resp.json()
    media_id = _extract_media_id(finalize_data)
    if not media_id:
        raise TikTokAPIError(f'Finalize succeeded but no media_id in response: {finalize_data}')
    return media_id


def create_post_from_media(media_id: str, caption: str, create_post_url: Optional[str] = None, access_token: Optional[str] = None) -> dict:
    create_post_url = create_post_url or os.getenv('TIKTOK_CREATE_POST_URL')
    if not create_post_url:
        raise TikTokAPIError('No create post URL configured (TIKTOK_CREATE_POST_URL)')

    headers = _auth_headers(access_token)
    headers['Content-Type'] = 'application/json'
    payload = {
        'media_id': media_id,
        'text': caption,
    }
    resp = requests.post(create_post_url, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise TikTokAPIError(f'Create post failed: {resp.status_code} {resp.text}')
    return resp.json()


def _extract_media_id(resp_json: dict) -> Optional[str]:
    # Try several common keys in API responses
    if not isinstance(resp_json, dict):
        return None
    data = resp_json.get('data') or resp_json
    if isinstance(data, dict):
        for key in ('media_id', 'mediaId', 'video_id', 'videoId', 'id'):
            if key in data:
                return data[key]
    # Top-level keys
    for key in ('media_id', 'mediaId', 'video_id', 'videoId', 'id'):
        if key in resp_json:
            return resp_json[key]
    return None
