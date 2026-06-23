"""Instagram posting helper (Instagram Graph API).

Requires:
- IG_ACCESS_TOKEN in environment (long-lived token)
- IG_USER_ID in environment

This is a minimal wrapper for direct publishing of video posts. See Instagram Graph API docs for full flows and permission scopes.
"""
import requests
import os


def upload_to_instagram(video_path: str, caption: str, access_token: str, ig_user_id: str):
    # Step 1: Upload container
    print('Uploading to Instagram...')
    # Upload endpoint for videos: https://graph.facebook.com/{api-version}/{ig-user-id}/media
    api_version = 'v17.0'
    upload_url = f'https://graph.facebook.com/{api_version}/{ig_user_id}/media'

    files = {
        # For the Graph API, large videos are recommended to be uploaded by URL (server pulls). This simple example uses a direct file upload which may not work for large files.
    }

    # Simple: use the container with 'media_type=VIDEO' and 'video_url' if you can host the file on an accessible URL.
    # Here we document the flow but do not implement a robust resumable upload.
    raise NotImplementedError('Direct video publishing requires hosting the video somewhere accessible or implementing chunked upload. See README for options.')
