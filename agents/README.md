TikTok Business API

This repository includes two ways to publish to TikTok:

1) Preferred: TikTok Business/Open API (stable and compliant)
   - Implemented as a scaffold in agents/poster_tiktok_api.py. You should provide an OAuth access token (TIKTOK_ACCESS_TOKEN)
     and, if needed, set TIKTOK_API_BASE to the correct API base URL for your app.
   - The scaffold includes functions to upload video (multipart) and create a post referencing the media id.
   - If you provide a valid access token the CLI will attempt the Business API path first.

2) Fallback: Browser automation (Playwright)
   - Implemented in agents/poster_tiktok_playwright.py. This is fragile and may violate TikTok's Terms of Service.
   - Use the interactive login helper agents/tiktok_login.py to generate a storage-state file and set TIKTOK_STORAGE_STATE to its path.

Environment variables for API-based uploads
- TIKTOK_ACCESS_TOKEN: OAuth access token for Business/Open API
- TIKTOK_API_BASE: Optional — override the base URL for the API if your app uses a different version/endpoint

If you want me to finalize the Business API integration, provide either:
- A test access token and the exact API endpoints your app uses (I will not store these in the repo), or
- The TikTok Business API documentation link for the authentication and upload endpoints your app should use.

I can then implement a complete, tested Business API uploader (resumable uploads, chunked upload, polling, and post creation).