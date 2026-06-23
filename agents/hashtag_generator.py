"""Hashtag and caption generator using OpenAI as the default LLM (configurable).

This module calls an LLM when OPENAI_API_KEY is set; otherwise it falls back to a simple heuristic.
Set OPENAI_API_KEY in your environment to enable high-quality captions and hashtags.
"""
import os
import re
from typing import List

try:
    import openai
except Exception:
    openai = None


def call_llm(prompt: str, max_tokens: int = 200) -> str:
    """Call the configured LLM. By default this uses OpenAI (OPENAI_API_KEY).

    Returns the text response or an empty string on failure (so callers can fallback).
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or openai is None:
        return ''

    model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    openai.api_key = api_key

    system_msg = (
        "You are a social media assistant that suggests short, engaging captions and trending hashtags "
        "for Instagram and TikTok posts. Produce concise results. For hashtags, include the hash (#) before words."
    )

    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        text = resp['choices'][0]['message']['content'].strip()
        return text
    except Exception as e:
        # Log to stdout for now; in production use structured logging
        print('LLM call failed:', e)
        return ''


def generate_hashtags(caption: str, top_k: int = 12) -> List[str]:
    # If an LLM is available, use it to propose hashtags.
    prompt = f"Generate {top_k} relevant and trending Instagram/TikTok hashtags for this caption:\n\n{caption}\n\nRespond with hashtags only, separated by spaces or newlines."
    response = call_llm(prompt)
    if response:
        tags = re.findall(r"#\w+", response)
        if tags:
            # Deduplicate while preserving order
            seen = set()
            out = []
            for t in tags:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    out.append(t)
                if len(out) >= top_k:
                    break
            return out

    # Fallback: crude keyword extraction
    words = re.findall(r"\w{4,}", caption.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda k: -freq[k])[:top_k]
    return [f"#{w}" for w in sorted_words]


def generate_caption(video_path: str) -> str:
    # Use the LLM to generate a caption based on the filename and a short instruction.
    base = os.path.basename(video_path)
    name, _ = os.path.splitext(base)
    prompt = (
        f"Write a short, attention-grabbing Instagram/TikTok caption (max 30 words) for a vertical short-form video titled '{name}'. "
        "Keep it punchy and include a call-to-action to watch till the end."
    )
    response = call_llm(prompt, max_tokens=60)
    if response:
        # Clean up any hashtags (they will be generated separately)
        return response.replace('\n', ' ').strip()

    return f"Check out this clip: {name} — watch till the end!"
