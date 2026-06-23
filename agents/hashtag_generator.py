"""Hashtag and caption generator using a pluggable LLM interface.

This module uses an LLM API if TTS/LLM credentials are provided, otherwise falls back to a simple heuristic.
Replace `call_llm` with your preferred LLM client (OpenAI, Anthropic, etc.).
"""
import os
import re
from typing import List


def call_llm(prompt: str, max_tokens: int = 200) -> str:
    # Placeholder: integrate your LLM of choice here. Example: OpenAI, Anthropic, or local LLM.
    # The environment variable LLM_API_KEY can be used by your wrapper.
    api_key = os.getenv('LLM_API_KEY')
    if not api_key:
        # No LLM key available — return an empty string to trigger fallback.
        return ''
    # TODO: call the LLM API and return the text.
    return ''


def generate_hashtags(caption: str, top_k: int = 12) -> List[str]:
    # If an LLM is available, use it to propose hashtags.
    prompt = f"Generate {top_k} relevant and trending Instagram/TikTok hashtags for this caption:\n\n{caption}\n\nHashtags:" 
    response = call_llm(prompt)
    if response:
        tags = re.findall(r"#\w+", response)
        if tags:
            return tags[:top_k]

    # Fallback: crude keyword extraction
    words = re.findall(r"\w{4,}", caption.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda k: -freq[k])[:top_k]
    return [f"#{w}" for w in sorted_words]


def generate_caption(video_path: str) -> str:
    # Placeholder function: could analyze frames, audio, or use a prompt describing the clip.
    base = os.path.basename(video_path)
    name, _ = os.path.splitext(base)
    return f"Check out this clip: {name} — watch till the end!"
