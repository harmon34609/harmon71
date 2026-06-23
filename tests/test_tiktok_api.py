"""Unit tests for the TikTok Business API uploader scaffold.

These tests use unittest.mock to simulate API responses and validate that the scaffold handles the
happy path and some error conditions. They do not perform real network calls.
"""
import io
import os
import unittest
from unittest.mock import patch, Mock

from agents import poster_tiktok_api as api


class TestTikTokAPIScaffold(unittest.TestCase):
    @patch('agents.poster_tiktok_api.requests.post')
    def test_multipart_upload_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'data': {'media_id': 'abc123'}}
        mock_post.return_value = mock_resp

        # Create a small temp file
        path = 'tests_temp_video.mp4'
        with open(path, 'wb') as f:
            f.write(b'0' * 1024)

        try:
            media_id = api.upload_video_multipart(path, multipart_url='https://example.com/upload', access_token='tk')
            self.assertEqual(media_id, 'abc123')
        finally:
            os.remove(path)

    @patch('agents.poster_tiktok_api.requests.post')
    @patch('agents.poster_tiktok_api.requests.put')
    def test_resumable_upload_and_finalize(self, mock_put, mock_post):
        # Init response
        init_resp = Mock()
        init_resp.status_code = 200
        init_resp.json.return_value = {'upload_id': 'uid123'}

        # Finalize response
        finalize_resp = Mock()
        finalize_resp.status_code = 200
        finalize_resp.json.return_value = {'data': {'media_id': 'm789'}}

        # Sequence of post() calls: first init, second finalize
        mock_post.side_effect = [init_resp, finalize_resp]

        # Mock put to accept chunk uploads
        put_resp = Mock()
        put_resp.status_code = 200
        mock_put.return_value = put_resp

        # Small file to force a single chunk
        path = 'tests_temp_video2.mp4'
        with open(path, 'wb') as f:
            f.write(b'1' * (1024 * 10))

        try:
            media_id = api.upload_video_resumable(path,
                                                 init_url='https://example.com/init',
                                                 chunk_url_template='https://example.com/upload/{upload_id}/{chunk_index}',
                                                 finalize_url='https://example.com/finalize',
                                                 access_token='tk',
                                                 chunk_size=1024 * 1024)
            self.assertEqual(media_id, 'm789')
        finally:
            os.remove(path)

    @patch('agents.poster_tiktok_api.requests.post')
    def test_create_post_from_media_missing_url(self, mock_post):
        with self.assertRaises(api.TikTokAPIError):
            api.create_post_from_media('m1', caption='hi', create_post_url=None)


if __name__ == '__main__':
    unittest.main()
