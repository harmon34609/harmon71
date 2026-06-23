"""Main orchestrator for the social agent prototype.

Usage examples:
  python agents/agent.py enhance input.mp4 output.mp4
  python agents/agent.py create_post input.mp4 "My caption" --publish --platform instagram

This is a minimal CLI that wires the building blocks together.
"""
import argparse
import os
from video_editor import enhance_video
from hashtag_generator import generate_hashtags, generate_caption
from poster_instagram import upload_to_instagram
from poster_tiktok import upload_to_tiktok


def cmd_enhance(args):
    print(f"Enhancing {args.input} -> {args.output}")
    enhance_video(args.input, args.output)
    print("Done.")


def cmd_create_post(args):
    # enhance first
    temp_out = args.input.replace('.mp4', '_enhanced.mp4')
    enhance_video(args.input, temp_out)

    caption = args.caption or generate_caption(temp_out)
    hashtags = generate_hashtags(caption, top_k=10)
    full_caption = caption + "\n\n" + " ".join(hashtags)

    print("Caption:\n", full_caption)

    if args.publish:
        if args.platform == 'instagram':
            token = os.getenv('IG_ACCESS_TOKEN')
            ig_user = os.getenv('IG_USER_ID')
            if not token or not ig_user:
                raise SystemExit("Set IG_ACCESS_TOKEN and IG_USER_ID in your environment to publish to Instagram")
            upload_to_instagram(temp_out, full_caption, token, ig_user)
        elif args.platform == 'tiktok':
            api_key = os.getenv('TIKTOK_API_KEY')
            if not api_key:
                raise SystemExit("Set TIKTOK_API_KEY in your environment to publish to TikTok")
            upload_to_tiktok(temp_out, full_caption, api_key)
        else:
            raise SystemExit("Unsupported platform")
    else:
        print("Publish flag not set. Local post created.")


def main():
    parser = argparse.ArgumentParser(description='Social agent prototype')
    sub = parser.add_subparsers(dest='cmd')

    p_enh = sub.add_parser('enhance')
    p_enh.add_argument('input')
    p_enh.add_argument('output')

    p_post = sub.add_parser('create_post')
    p_post.add_argument('input')
    p_post.add_argument('--caption', default=None)
    p_post.add_argument('--publish', action='store_true')
    p_post.add_argument('--platform', choices=['instagram','tiktok'], default='instagram')

    args = parser.parse_args()
    if args.cmd == 'enhance':
        cmd_enhance(args)
    elif args.cmd == 'create_post':
        cmd_create_post(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
