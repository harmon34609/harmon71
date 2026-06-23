# Social agent prototype for harmon71

This directory contains a prototype agent that can enhance videos, generate hashtags/captions using OpenAI, and (with proper credentials) post to Instagram and TikTok. Replace placeholder credentials with real ones and follow the README for setup.

Environment variables
- OPENAI_API_KEY: (optional) If set, the agent will use OpenAI to generate higher-quality captions and hashtags. You can also set LLM_MODEL (e.g. gpt-4o-mini or gpt-3.5-turbo) to choose a different model.
- IG_ACCESS_TOKEN and IG_USER_ID: required if you implement Instagram publishing and use --publish.
- TIKTOK_API_KEY: required if you implement TikTok Business API posting.

Quick start
1) Install requirements:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Use the CLI:
   python agents/agent.py enhance path/to/input.mp4 path/to/output_enhanced.mp4
   python agents/agent.py create_post path/to/input.mp4 --caption "My caption"

Notes
- The OpenAI integration requires a valid OPENAI_API_KEY. The code uses the OpenAI Python client to call ChatCompletion (gpt-3.5-turbo by default).
- Posting to Instagram/TikTok remains a placeholder. I can implement those flows if you provide API access or instruct me to add an automation fallback.
