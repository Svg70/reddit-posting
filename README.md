# Reddit Auto-Post Script

Simple Python script for automated posting to Reddit using OAuth2 API.

## Features

- OAuth2 authentication with Reddit API
- Post text posts, links, and media (images/videos) to subreddits
- Simple Flask API server for content review and posting
- Proper rate limiting and error handling

## Installation

pip install -r requirements.txt## Configuration

1. Copy `reddit_config.example.json` to `reddit_config.json`
2. Fill in your Reddit API credentials:
   - Get API keys from https://www.reddit.com/prefs/apps
   - Create a "script" type application
   - Copy `client_id` and `client_secret`
   - Add your Reddit `username` and `password`
   - Set `user_agent` in format: `AppName/1.0 (by /u/username)`

## Usage

### Run as API Server

python reddit_autopost.pyServer starts on `http://0.0.0.0:5000`

### API Endpoints

**POST /post** - Post to Reddit

Request body (JSON):
{
  "title": "Post title",
  "text": "Post text (for text posts)",
  "url": "https://example.com (for link posts)",
  "media_url": "https://example.com/image.jpg (for media posts)",
  "subreddit": "test",
  "post_type": "self|link|media (optional, auto-detected)",
  "flair_id": "optional_flair_id"
}Response:
{
  "success": true,
  "post_id": "abc123",
  "post_name": "t3_abc123",
  "url": "https://reddit.com/r/test/comments/..."
}**GET /health** - Health check

## Example

curl -X POST http://localhost:5000/post \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Post",
    "text": "Post content",
    "subreddit": "test"
  }'## Requirements

- Python 3.7+
- Reddit API credentials (client_id, client_secret)
- Reddit account with posting permissions

## License

Personal use only.