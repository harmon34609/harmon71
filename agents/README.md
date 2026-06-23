Updated README: how to configure the TikTok Business API endpoints for resumable or multipart uploads.

Key environment variables you can set to enable the Business API flow (examples):

# Simple multipart upload (if your API supports it)
export TIKTOK_API_MULTIPART_UPLOAD_URL="https://api.example.com/v1/video/upload"
export TIKTOK_ACCESS_TOKEN="<your-token>"

# Resumable/chunked upload (recommended for large files)
export TIKTOK_API_INIT_UPLOAD_URL="https://api.example.com/v1/video/resumable/init"
export TIKTOK_API_UPLOAD_CHUNK_URL="https://api.example.com/v1/video/resumable/{upload_id}/chunk/{chunk_index}"
export TIKTOK_API_FINALIZE_UPLOAD_URL="https://api.example.com/v1/video/resumable/finalize"
export TIKTOK_CREATE_POST_URL="https://api.example.com/v1/video/post/create"
export TIKTOK_ACCESS_TOKEN="<your-token>"

Notes:
- The scaffold will attempt the Business API upload when TIKTOK_ACCESS_TOKEN and the relevant endpoints are set.
- If the API path fails or isn't configured, the agent falls back to the Playwright browser automation method.
- If you can provide a test access token or the specific TikTok Business/OpenAPI documentation links for the API your app uses, I can map these scaffold endpoints to the exact final implementation and add integration tests.
