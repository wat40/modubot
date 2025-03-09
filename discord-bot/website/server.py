import http.server
import socketserver
import os
import webbrowser
import json
import urllib.parse
import urllib.request
import secrets
import ssl
import traceback
from threading import Timer

# Configuration
PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# OAuth Configuration
CLIENT_ID = "1348106326131081216"  # Replace with your Discord application client ID
CLIENT_SECRET = "q0AcOzuCt2INmVwXm-z6NLgRQtzZElho"  # In a real app, this should be securely stored in environment variables
REDIRECT_URI = f"http://localhost:{PORT}/oauth/callback"
OAUTH_STATE = secrets.token_urlsafe(32)  # CSRF protection token
OAUTH_SCOPE = "identify guilds"

# Store temporary tokens
tokens = {}

class WebsiteHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """Override to add color and better formatting to log messages"""
        GREEN = "\033[92m"
        RESET = "\033[0m"
        BOLD = "\033[1m"
        print(f"{GREEN}{BOLD}[SERVER]{RESET} {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests including OAuth callback"""
        # Parse the URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Debug logging
        print(f"Path requested: {path}")
        
        # Handle specific routes BEFORE trying to serve static files
        try:
            if path == '/oauth/login':
                print("Handling OAuth login...")
                self.handle_oauth_login()
                return  # Important: return after handling to prevent file lookup
            elif path == '/oauth/callback':
                print("Handling OAuth callback...")
                self.handle_oauth_callback()
                return  # Important: return after handling to prevent file lookup
            elif path == '/api/user':
                print("Handling user info request...")
                self.handle_user_info()
                return  # Important: return after handling to prevent file lookup
            elif path == '/api/guilds':
                print("Handling guilds request...")
                self.handle_user_guilds()
                return  # Important: return after handling to prevent file lookup
            elif path == '/':
                # Redirect root to dashboard
                self.send_response(302)
                self.send_header('Location', '/dashboard.html')
                self.end_headers()
                return
                
            # If none of the special routes matched, try to serve a static file
            super().do_GET()
        except Exception as e:
            print(f"Error handling request for {path}: {str(e)}")
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def handle_oauth_login(self):
        """Redirect to Discord OAuth authorization page"""
        try:
            print("Building OAuth URL...")
            # Build the OAuth URL
            oauth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope={urllib.parse.quote(OAUTH_SCOPE)}&state={OAUTH_STATE}"
            
            print(f"Redirecting to OAuth URL: {oauth_url}")
            # Send redirect response
            self.send_response(302)
            self.send_header('Location', oauth_url)
            self.end_headers()
            print("Redirect sent successfully")
        except Exception as e:
            print(f"Error in handle_oauth_login: {str(e)}")
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def handle_oauth_callback(self):
        """Handle OAuth callback from Discord"""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            # Check state for CSRF protection
            if 'state' not in params or params['state'][0] != OAUTH_STATE:
                print("Invalid state parameter in callback")
                self.send_error(400, "Invalid state parameter")
                return
            
            if 'code' not in params:
                print("No authorization code received in callback")
                self.send_error(400, "No authorization code received")
                return
            
            code = params['code'][0]
            
            # Exchange code for access token
            token_url = "https://discord.com/api/oauth2/token"
            data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'scope': OAUTH_SCOPE
            }
            
            # Print debug info about the request we're about to make
            print(f"Requesting token from {token_url}")
            print(f"Using client_id: {CLIENT_ID}")
            print(f"Using redirect_uri: {REDIRECT_URI}")
            
            try:
                data = urllib.parse.urlencode(data).encode()
                req = urllib.request.Request(token_url, data=data, method="POST")
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
                
                # Handle SSL certificate validation
                context = ssl.create_default_context()
                
                print("Sending request to Discord API...")
                response = urllib.request.urlopen(req, context=context)
                token_data = json.loads(response.read().decode())
                
                # Store token (in a real app, you would use a more secure method)
                user_token = token_data['access_token']
                tokens['discord_token'] = user_token
                
                print(f"Successfully received token. Redirecting to dashboard.")
                # Redirect to dashboard with success
                self.send_response(302)
                self.send_header('Location', '/dashboard.html?login_success=true')
                self.end_headers()
                
            except urllib.error.HTTPError as e:
                error_body = e.read().decode()
                print(f"HTTP Error exchanging code for token: {e.code} - {e.reason}")
                print(f"Error details: {error_body}")
                
                # For the demo, handle invalid client secret gracefully
                if "invalid client" in error_body.lower():
                    self.send_response(302)
                    self.send_header('Location', '/dashboard.html?login_error=invalid_client')
                    self.end_headers()
                    print("This is expected in demo mode. In a real app, you'd need a valid Discord client secret.")
                else:
                    self.send_error(500, f"Failed to obtain access token: {e.reason}")
            except Exception as e:
                print(f"Error exchanging code for token: {str(e)}")
                traceback.print_exc()
                self.send_error(500, f"Failed to obtain access token: {str(e)}")
        except Exception as e:
            print(f"Error in handle_oauth_callback: {str(e)}")
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def handle_user_info(self):
        """Return user information from Discord API"""
        try:
            if 'discord_token' not in tokens:
                print("No token available for user info request")
                self.send_error(401, "Not authenticated")
                return
            
            try:
                req = urllib.request.Request("https://discord.com/api/v10/users/@me")
                req.add_header('Authorization', f"Bearer {tokens['discord_token']}")
                
                context = ssl.create_default_context()
                response = urllib.request.urlopen(req, context=context)
                user_data = json.loads(response.read().decode())
                
                print(f"Successfully fetched user data for {user_data.get('username', 'unknown user')}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(user_data).encode())
                
            except urllib.error.HTTPError as e:
                print(f"HTTP Error fetching user data: {e.code} - {e.reason}")
                if e.code == 401:
                    self.send_error(401, "Authentication token expired or invalid")
                else:
                    self.send_error(e.code, e.reason)
            except Exception as e:
                print(f"Error fetching user data: {str(e)}")
                traceback.print_exc()
                self.send_error(500, f"Failed to get user information: {str(e)}")
        except Exception as e:
            print(f"Error in handle_user_info: {str(e)}")
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def handle_user_guilds(self):
        """Return user's guilds from Discord API"""
        try:
            if 'discord_token' not in tokens:
                print("No token available for guilds request")
                self.send_error(401, "Not authenticated")
                return
            
            try:
                req = urllib.request.Request("https://discord.com/api/v10/users/@me/guilds")
                req.add_header('Authorization', f"Bearer {tokens['discord_token']}")
                
                context = ssl.create_default_context()
                response = urllib.request.urlopen(req, context=context)
                guilds_data = json.loads(response.read().decode())
                
                print(f"Successfully fetched guild data: {len(guilds_data)} guilds found")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(guilds_data).encode())
                
            except urllib.error.HTTPError as e:
                print(f"HTTP Error fetching guilds data: {e.code} - {e.reason}")
                if e.code == 401:
                    self.send_error(401, "Authentication token expired or invalid")
                else:
                    self.send_error(e.code, e.reason)
            except Exception as e:
                print(f"Error fetching guilds data: {str(e)}")
                traceback.print_exc()
                self.send_error(500, f"Failed to get guilds information: {str(e)}")
        except Exception as e:
            print(f"Error in handle_user_guilds: {str(e)}")
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {str(e)}")

def open_browser():
    """Open the default web browser to the server URL"""
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    # Create a TCP socket server
    handler = WebsiteHandler
    
    # Check if the port is available and try alternatives if needed
    current_port = PORT
    server = None
    
    for attempt in range(10):  # Try ports from PORT to PORT+10
        try:
            server = socketserver.TCPServer(("", current_port), handler)
            break
        except OSError:
            print(f"Port {current_port} is in use, trying {current_port + 1}...")
            current_port += 1
    
    if not server:
        print("Could not find an available port. Please close other applications using these ports.")
        return

    global REDIRECT_URI
    if current_port != PORT:
        # Update redirect URI if port changed
        REDIRECT_URI = REDIRECT_URI.replace(f":{PORT}", f":{current_port}")
    
    # Display startup message
    print(f"\n{'='*60}")
    print(f"ModuBot Website - Local Development Server")
    print(f"{'='*60}")
    print(f"Server started at http://localhost:{current_port}")
    print(f"OAuth login URL: http://localhost:{current_port}/oauth/login")
    print(f"OAuth callback URL: {REDIRECT_URI}")
    print(f"Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    # Open browser after a short delay
    Timer(1.0, open_browser).start()
    
    try:
        # Start the server and keep it running until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()
        print("Server stopped")

if __name__ == "__main__":
    main() 