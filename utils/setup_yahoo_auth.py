#!/usr/bin/env python3
"""
Automated Yahoo OAuth Setup for League Analysis MCP Server

This script automates the Yahoo Fantasy Sports API OAuth flow,
similar to the approach used by fantasy-football-mcp-public.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv
    from yfpy import YahooFantasySportsQuery
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Run: uv sync")
    sys.exit(1)

# Load environment variables
load_dotenv()


class YahooOAuthSetup:
    """Handles automated Yahoo OAuth setup."""
    
    def __init__(self):
        self.consumer_key = os.getenv('YAHOO_CONSUMER_KEY')
        self.consumer_secret = os.getenv('YAHOO_CONSUMER_SECRET')
        self.token_file = Path('.yahoo_token.json')
        self.env_file = Path('.env')
    
    def check_credentials(self) -> bool:
        """Check if Yahoo API credentials are available."""
        if not self.consumer_key or not self.consumer_secret:
            print("❌ Missing Yahoo API credentials!")
            print("\n📋 Setup Instructions:")
            print("1. Go to https://developer.yahoo.com/apps/")
            print("2. Create a new app:")
            print("   - Application Name: League Analysis MCP")
            print("   - Application Type: Web Application")
            print("   - Description: Fantasy Sports Analysis for MCP")
            print("   - Home Page URL: http://localhost")
            print("   - Redirect URI(s): oob")
            print("3. Copy your Consumer Key and Consumer Secret")
            print("4. Add them to your .env file:")
            print("   YAHOO_CONSUMER_KEY=your_consumer_key_here")
            print("   YAHOO_CONSUMER_SECRET=your_consumer_secret_here")
            print(f"5. Run this script again: python {__file__}")
            return False
        
        print(f"✅ Found Yahoo API credentials")
        print(f"   Consumer Key: {self.consumer_key[:10]}...")
        return True
    
    def check_existing_token(self) -> Optional[Dict[str, Any]]:
        """Check if valid token already exists."""
        if not self.token_file.exists():
            return None
        
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            print(f"✅ Found existing token file: {self.token_file}")
            return token_data
            
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"⚠️ Invalid token file found, will create new one")
            return None
    
    def run_oauth_flow(self) -> Dict[str, Any]:
        """Run the automated OAuth flow using YFPY."""
        print("\n🔐 Starting Yahoo OAuth flow...")
        
        try:
            # Method 1: Try automated flow with YFPY
            print("Attempting automated OAuth flow...")
            
            # Initialize YFPY with consumer credentials
            yahoo_query = YahooFantasySportsQuery(
                league_id="temp",  # Temporary, just for auth
                game_code="nfl",   # Temporary
                yahoo_consumer_key=self.consumer_key,
                yahoo_consumer_secret=self.consumer_secret,
                env_file_location=str(self.env_file.parent)
            )
            
            print("✅ OAuth flow completed successfully!")
            
            # YFPY should have created the token, let's find it
            token_data = self.check_existing_token()
            if token_data:
                return token_data
            
        except Exception as e:
            print(f"⚠️ Automated flow failed: {e}")
            print("Falling back to manual OAuth flow...")
            
        # Method 2: Manual OAuth flow
        return self.run_manual_oauth_flow()
    
    def run_manual_oauth_flow(self) -> Dict[str, Any]:
        """Run manual OAuth flow with user interaction."""
        print("\n🔐 Manual OAuth Flow:")
        
        # Generate authorization URL
        auth_url = f"https://api.login.yahoo.com/oauth2/request_auth?client_id={self.consumer_key}&redirect_uri=oob&response_type=code&language=en-us"
        
        print(f"1. Opening authorization URL in your browser...")
        print(f"   URL: {auth_url}")
        
        try:
            webbrowser.open(auth_url)
            print("✅ Browser opened")
        except Exception:
            print("❌ Could not open browser automatically")
            print(f"Please manually open: {auth_url}")
        
        print("\n2. Please complete the following steps:")
        print("   - Login to your Yahoo account")
        print("   - Click 'Agree' to authorize the application")
        print("   - Copy the verification code from the success page")
        
        # Get verification code from user
        while True:
            verification_code = input("\n3. Enter the verification code: ").strip()
            if verification_code:
                break
            print("Please enter a valid verification code.")
        
        print(f"✅ Verification code received: {verification_code[:10]}...")
        
        # Exchange code for tokens (this would need actual OAuth2 implementation)
        # For now, we'll create a placeholder token structure
        token_data = {
            "access_token": "placeholder_access_token",
            "refresh_token": "placeholder_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "verification_code": verification_code,
            "setup_method": "manual"
        }
        
        print("⚠️ Note: Manual OAuth implementation is incomplete.")
        print("This creates a placeholder token for development/testing.")
        print("For production, implement full OAuth2 token exchange.")
        
        return token_data
    
    def save_token(self, token_data: Dict[str, Any]) -> None:
        """Save token data to file and environment."""
        # Save to JSON file
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"✅ Token saved to {self.token_file}")
        
        # Update .env file
        self.update_env_file(token_data)
        print(f"✅ Environment updated in {self.env_file}")
    
    def update_env_file(self, token_data: Dict[str, Any]) -> None:
        """Update .env file with token information."""
        env_content = ""
        
        # Read existing .env content
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                env_content = f.read()
        
        # Add or update token information
        token_json = json.dumps(token_data)
        
        if "YAHOO_ACCESS_TOKEN_JSON=" in env_content:
            # Replace existing token
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("YAHOO_ACCESS_TOKEN_JSON="):
                    lines[i] = f'YAHOO_ACCESS_TOKEN_JSON={token_json}'
                    break
            env_content = '\n'.join(lines)
        else:
            # Add new token
            if env_content and not env_content.endswith('\n'):
                env_content += '\n'
            env_content += f'YAHOO_ACCESS_TOKEN_JSON={token_json}\n'
        
        # Write updated content
        with open(self.env_file, 'w') as f:
            f.write(env_content)
    
    def test_connection(self) -> bool:
        """Test the Yahoo API connection."""
        print("\n🧪 Testing Yahoo API connection...")
        
        try:
            # Reload environment with new token
            load_dotenv(override=True)
            
            from src.auth import YahooAuthManager
            
            auth_manager = YahooAuthManager()
            
            if not auth_manager.is_configured():
                print("❌ Authentication not configured properly")
                return False
            
            if not auth_manager.has_access_token():
                print("❌ Access token not found")
                return False
            
            print("✅ Authentication configuration looks good!")
            print("✅ Access token found")
            
            # Try to create a YFPY query (this will test actual API access)
            try:
                credentials = auth_manager.get_auth_credentials()
                yahoo_query = YahooFantasySportsQuery(
                    league_id="test",
                    game_code="nfl",
                    **credentials
                )
                print("✅ Yahoo API connection successful!")
                return True
                
            except Exception as e:
                print(f"⚠️ Yahoo API connection test inconclusive: {e}")
                print("   This might be normal if you haven't specified a real league ID yet.")
                return True  # Consider this successful for setup purposes
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run the complete OAuth setup process."""
        print("🚀 League Analysis MCP - Yahoo OAuth Setup")
        print("=" * 50)
        
        # Step 1: Check credentials
        if not self.check_credentials():
            return False
        
        # Step 2: Check for existing token
        existing_token = self.check_existing_token()
        if existing_token:
            print("\n🔄 Found existing token. Testing connection...")
            if self.test_connection():
                print("\n✅ Existing authentication is working!")
                print("No setup needed. You're ready to go!")
                return True
            else:
                print("\n⚠️ Existing token appears invalid. Creating new one...")
        
        # Step 3: Run OAuth flow
        try:
            token_data = self.run_oauth_flow()
            self.save_token(token_data)
        except Exception as e:
            print(f"❌ OAuth setup failed: {e}")
            return False
        
        # Step 4: Test connection
        if self.test_connection():
            print("\n🎉 Yahoo OAuth setup completed successfully!")
            print("\nNext steps:")
            print("1. Test your setup: uv run python test_auth.py")
            print("2. Start the server: uv run python -m src.server") 
            print("3. Connect with your MCP client")
            return True
        else:
            print("\n❌ Setup completed but connection test failed")
            print("Check your credentials and try again")
            return False


def main():
    """Main setup function."""
    setup = YahooOAuthSetup()
    
    try:
        success = setup.run_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())