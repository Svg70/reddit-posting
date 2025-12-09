import os
import sys
import json
import base64
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import mimetypes
from flask import Flask, request, jsonify


class RedditAutoPoster:
    """
    Class for automatic posting to Reddit.
    
    Complies with Reddit API requirements:
    - Uses OAuth2 for authentication
    - Properly configured User-Agent
    - Respects rate limits
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit Auto Poster.
        
        Args:
            client_id: Client ID from Reddit application settings
            client_secret: Client Secret from Reddit application settings
            username: Reddit username
            password: Reddit password
            user_agent: User-Agent string (format: "AppName/Version by /u/username")
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        # User-Agent must be unique and describe the application
        # Format: "AppName/Version by /u/username"
        if user_agent is None:
            self.user_agent = f"LivePosting/1.0 (by /u/{username})"
        else:
            self.user_agent = user_agent
        
        self.access_token: Optional[str] = None
        self.token_type: str = "bearer"
        
        # Reddit API endpoints
        self.token_url = "https://www.reddit.com/api/v1/access_token"
        self.api_base = "https://oauth.reddit.com"
    
    def authenticate(self) -> bool:
        """
        Get OAuth2 access token from Reddit.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Prepare data for OAuth2
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'bearer')
                print(f"✓ Successfully authenticated with Reddit")
                return True
            else:
                error_msg = response.text
                print(f"✗ Authentication error: {response.status_code}")
                print(f"  Response: {error_msg}")
                return False
                
        except Exception as e:
            print(f"✗ Exception during authentication: {str(e)}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary with headers
        """
        if not self.access_token:
            raise ValueError("Authentication required first")
        
        return {
            'Authorization': f'{self.token_type.capitalize()} {self.access_token}',
            'User-Agent': self.user_agent,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def post_text(
        self,
        subreddit: str,
        title: str,
        text: str,
        flair_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Post a text post to Reddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            text: Post text
            flair_id: Flair ID (optional)
        
        Returns:
            Dictionary with API response data or None on error
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            data = {
                'api_type': 'json',
                'sr': subreddit,
                'title': title,
                'text': text,
                'kind': 'self'
            }
            
            if flair_id:
                data['flair_id'] = flair_id
            
            response = requests.post(
                f'{self.api_base}/api/submit',
                headers=self._get_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('json', {}).get('errors'):
                    errors = result['json']['errors']
                    print(f"✗ Error publishing: {errors}")
                    return None
                
                post_data = result.get('json', {}).get('data', {})
                post_id = post_data.get('id')
                post_name = post_data.get('name')
                print(f"✓ Post successfully published: {post_name}")
                return result
            else:
                print(f"✗ Error publishing: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Exception during publishing: {str(e)}")
            return None
    
    def post_link(
        self,
        subreddit: str,
        title: str,
        url: str,
        text: Optional[str] = None,
        flair_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Post a link to Reddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            url: Link URL
            text: Additional text (optional)
            flair_id: Flair ID (optional)
        
        Returns:
            Dictionary with API response data or None on error
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            data = {
                'api_type': 'json',
                'sr': subreddit,
                'title': title,
                'url': url,
                'kind': 'link'
            }
            
            if text:
                data['text'] = text
            
            if flair_id:
                data['flair_id'] = flair_id
            
            response = requests.post(
                f'{self.api_base}/api/submit',
                headers=self._get_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('json', {}).get('errors'):
                    errors = result['json']['errors']
                    print(f"✗ Error publishing: {errors}")
                    return None
                
                post_data = result.get('json', {}).get('data', {})
                post_name = post_data.get('name')
                print(f"✓ Link successfully published: {post_name}")
                return result
            else:
                print(f"✗ Error publishing: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Exception during publishing: {str(e)}")
            return None
    
    def _upload_media(self, media_url: str) -> Optional[str]:
        """
        Upload media file to Reddit.
        
        Args:
            media_url: Media file URL
        
        Returns:
            URL of uploaded media or None on error
        """
        try:
            # Step 1: Get upload lease
            filename = media_url.split('/')[-1] or 'media.jpg'
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'image/jpeg' if not filename.endswith('.mp4') else 'video/mp4'
            
            lease_data = {
                'filepath': filename,
                'mimetype': mime_type
            }
            
            response = requests.post(
                f'{self.api_base}/api/media/asset',
                headers=self._get_headers(),
                data=lease_data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"✗ Error getting upload lease: {response.status_code}")
                return None
            
            lease_result = response.json()
            args = lease_result.get('args', {})
            action = args.get('action')
            fields = args.get('fields', [])
            
            if not action or not fields:
                print("✗ Invalid response format from Reddit API")
                return None
            
            # Step 2: Download file
            print(f"  Downloading media: {filename}")
            media_response = requests.get(media_url, timeout=60)
            if media_response.status_code != 200:
                print(f"✗ Error downloading media file: {media_response.status_code}")
                return None
            
            # Step 3: Upload to Reddit
            files = {'file': (filename, media_response.content, mime_type)}
            upload_data = {}
            for field in fields:
                upload_data[field['name']] = field['value']
            
            upload_response = requests.post(
                f"https:{action}",
                data=upload_data,
                files=files,
                timeout=120
            )
            
            if upload_response.status_code != 200:
                print(f"✗ Error uploading to Reddit: {upload_response.status_code}")
                return None
            
            # Parse location from XML response
            response_text = upload_response.text
            if '<Location>' in response_text:
                start = response_text.find('<Location>') + 10
                end = response_text.find('</Location>')
                location = response_text[start:end]
                print(f"  ✓ Media uploaded: {location}")
                return location
            else:
                print("✗ Failed to find Location in response")
                return None
                
        except Exception as e:
            print(f"✗ Exception during media upload: {str(e)}")
            return None
    
    def post_media(
        self,
        subreddit: str,
        title: str,
        media_url: str,
        text: Optional[str] = None,
        flair_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Post a media post (image or video) to Reddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            media_url: Media file URL
            text: Additional text (optional)
            flair_id: Flair ID (optional)
        
        Returns:
            Dictionary with API response data or None on error
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            # Upload media
            uploaded_url = self._upload_media(media_url)
            if not uploaded_url:
                return None
            
            # Determine media type
            is_video = media_url.lower().endswith('.mp4') or 'video' in media_url.lower()
            kind = 'video' if is_video else 'image'
            
            data = {
                'api_type': 'json',
                'sr': subreddit,
                'title': title,
                'url': uploaded_url,
                'kind': kind,
                'text': text or ''
            }
            
            if flair_id:
                data['flair_id'] = flair_id
            
            response = requests.post(
                f'{self.api_base}/api/submit',
                headers=self._get_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('json', {}).get('errors'):
                    errors = result['json']['errors']
                    print(f"✗ Error publishing: {errors}")
                    return None
                
                post_data = result.get('json', {}).get('data', {})
                post_name = post_data.get('name')
                print(f"✓ Media post successfully published: {post_name}")
                return result
            else:
                print(f"✗ Error publishing: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Exception during publishing: {str(e)}")
            return None


def load_config(config_path: str = 'reddit_config.json') -> Dict[str, str]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Dictionary with configuration
    """
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create example configuration
        example_config = {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "username": "YOUR_USERNAME",
            "password": "YOUR_PASSWORD",
            "user_agent": "LivePosting/1.0 (by /u/YOUR_USERNAME)",
            "default_subreddit": "test"
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        print(f"✓ Created configuration file: {config_path}")
        print("  Fill it with your data before using")
        return example_config


# Global poster instance
poster: Optional[RedditAutoPoster] = None


def init_poster():
    """Initialize Reddit poster from configuration."""
    global poster
    config = load_config()
    
    # Check configuration
    required_keys = ['client_id', 'client_secret', 'username', 'password']
    missing_keys = [key for key in required_keys if config.get(key) == f'YOUR_{key.upper()}']
    
    if missing_keys:
        raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
    
    user_agent = config.get('user_agent')
    poster = RedditAutoPoster(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        username=config['username'],
        password=config['password'],
        user_agent=user_agent
    )
    
    # Authenticate
    if not poster.authenticate():
        raise ValueError("Failed to authenticate with Reddit")
    
    return poster


# Flask app
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/post', methods=['POST'])
def post_to_reddit():
    """
    API endpoint to post to Reddit.
    
    Expected JSON body:
    {
        "title": "Post title",
        "text": "Post text (for text posts)",
        "url": "https://example.com (for link posts)",
        "media_url": "https://example.com/image.jpg (for media posts)",
        "subreddit": "test (optional, uses default from config)",
        "post_type": "self|link|media (optional, auto-detected)",
        "flair_id": "optional_flair_id"
    }
    
    Returns:
        JSON response with post data or error message
    """
    global poster
    
    if poster is None:
        try:
            init_poster()
        except Exception as e:
            return jsonify({"error": f"Failed to initialize poster: {str(e)}"}), 500
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Required fields
        title = data.get('title')
        if not title:
            return jsonify({"error": "Missing required field: title"}), 400
        
        # Get subreddit (use default from config if not provided)
        subreddit = data.get('subreddit')
        if not subreddit:
            config = load_config()
            subreddit = config.get('default_subreddit', 'test')
        
        # Determine post type
        post_type = data.get('post_type')
        text = data.get('text', '')
        url = data.get('url')
        media_url = data.get('media_url')
        flair_id = data.get('flair_id')
        
        result = None
        
        # Auto-detect post type if not specified
        if not post_type:
            if media_url:
                post_type = 'media'
            elif url:
                post_type = 'link'
            else:
                post_type = 'self'
        
        # Publish based on type
        if post_type == 'media' and media_url:
            result = poster.post_media(
                subreddit=subreddit,
                title=title,
                media_url=media_url,
                text=text,
                flair_id=flair_id
            )
        elif post_type == 'link' and url:
            result = poster.post_link(
                subreddit=subreddit,
                title=title,
                url=url,
                text=text,
                flair_id=flair_id
            )
        else:
            # Default to text post
            result = poster.post_text(
                subreddit=subreddit,
                title=title,
                text=text,
                flair_id=flair_id
            )
        
        if result:
            post_data = result.get('json', {}).get('data', {})
            return jsonify({
                "success": True,
                "post_id": post_data.get('id'),
                "post_name": post_data.get('name'),
                "url": f"https://reddit.com{post_data.get('permalink', '')}"
            }), 200
        else:
            return jsonify({"error": "Failed to publish post"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """
    Main function to run Flask API server.
    """
    print("=" * 60)
    print("Reddit Auto-Posting API Server")
    print("=" * 60)
    print()
    
    try:
        # Initialize poster
        print("Initializing Reddit poster...")
        init_poster()
        print("✓ Reddit poster initialized successfully")
        print()
        print("API Endpoints:")
        print("  GET  /health - Health check")
        print("  POST /post   - Post to Reddit")
        print()
        print("Example POST /post request:")
        print("  {")
        print('    "title": "My Post Title",')
        print('    "text": "Post content",')
        print('    "subreddit": "test"')
        print("  }")
        print()
        print("Starting server on http://0.0.0.0:5000")
        print("=" * 60)
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

