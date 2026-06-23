"""Simple video enhancement utilities.

This is a lightweight, best-effort implementation using ffmpeg via subprocess and moviepy where helpful.
Requirements: ffmpeg must be installed on the system and available on PATH.
"""
import subprocess
import shutil
import os
from moviepy.editor import VideoFileClip


def enhance_video(input_path: str, output_path: str, target_bitrate: str = '2500k'):
    """Run a short ffmpeg pipeline to adjust exposure/color and apply light denoise.
    This function creates a temporary processed file and writes output_path.
    """
    if not shutil.which('ffmpeg'):
        raise RuntimeError('ffmpeg is required on PATH')

    # Basic color/brightness/saturation adjustment and denoise (hqdn3d)
    # eq=brightness:contrast:saturation
    # Example values tuned for small improvements; adjust as-needed or implement auto-meters.
    eq = 'eq=brightness=0.05:contrast=1.05:saturation=1.05'
    denoise = 'hqdn3d=1.5:1.5:6:6'

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f"{eq},{denoise}",
        '-b:v', target_bitrate,
        '-preset', 'fast',
        output_path
    ]

    print('Running ffmpeg command:',' '.join(cmd))
    subprocess.run(cmd, check=True)


def extract_clip(input_path: str, start: float, end: float, out_path: str):
    with VideoFileClip(input_path) as clip:
        sub = clip.subclip(start, end)
        sub.write_videofile(out_path, codec='libx264', audio_codec='aac')

