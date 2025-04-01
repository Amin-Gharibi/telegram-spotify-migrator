from os import getenv
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from spotipy import SpotifyOAuth, Spotify
import json


def get_spotify_user_id():
    print("\n===== Spotify User ID Retrieval =====")
    try:
        # Define scopes
        scopes = ["playlist-modify-private", "playlist-modify-public", "user-read-private"]

        # Set up Spotify OAuth
        print("Setting up Spotify OAuth...")
        sp_oauth = SpotifyOAuth(
            client_id=getenv("SPOTIFY_CLIENT_ID"),
            client_secret=getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=getenv("SPOTIFY_REDIRECT_URI"),
            scope=scopes,
            cache_path=None,  # Don't use cache file since we use session_tokens.json
            open_browser=False
        )

        # Generate the authorization URL
        auth_url = sp_oauth.get_authorize_url()

        print("\n===== Spotify Authorization =====")
        print("1. Open this URL in your browser and log in:")
        print(auth_url)
        print("2. After logging in, you will be redirected.")
        redirected_url = input("3. Paste the redirected URL here: ")

        # Extract authorization code from the redirected URL
        print("\nExtracting authorization code...")
        code = sp_oauth.parse_response_code(redirected_url)

        if not code:
            raise ValueError("Authorization code not found in the URL.")
        
        # Exchange the authorization code for an access token
        print("Exchanging authorization code for access token...")
        token_info = sp_oauth.get_access_token(code)

        # Save the token info to session_tokens.json
        save_token_info(token_info)
        print("Spotify token saved to session_tokens.json")

        # Initialize Spotify API with the access token
        print("Initializing Spotify API...")
        sp = Spotify(auth=token_info["access_token"])

        # Fetch user info
        print("Fetching user information...")
        user_info = sp.current_user()
        user_id = user_info["id"]

        print("\n===== Spotify User ID Result =====")
        print(f"Your Spotify User ID is: {user_id}")
        print("\nAdd this to your .env file as:")
        print(f"SPOTIFY_USER_ID={user_id}")
        return user_id

    except Exception as e:
        print(f"\n===== Error =====")
        print(f"Error retrieving Spotify User ID: {e}")
        exit(1)


def save_token_info(token_info):
    """Save token info to session_tokens.json"""
    try:
        # Load existing tokens
        try:
            with open("./session_tokens.json", "r") as session_file:
                tokens = json.loads(session_file.read())
        except (FileNotFoundError, json.JSONDecodeError):
            tokens = {"telegram": ""}
        
        # Update tokens
        tokens["spotify"] = token_info.get("access_token", "")
        tokens["spotify_refresh"] = token_info.get("refresh_token", "")
        tokens["spotify_expires_at"] = token_info.get("expires_at", 0)
        
        # Save updated tokens
        with open("./session_tokens.json", "w") as session_file:
            session_file.write(json.dumps(tokens))
            
    except Exception as e:
        print(f"Error saving token info: {e}")


def calculate_similarity(text1, text2):
    """
    Calculate similarity between two strings using Levenshtein distance.
    Returns a value between 0 (completely different) and 1 (identical).
    """
    # Lowercase for better comparison
    text1 = text1.lower()
    text2 = text2.lower()

    # Calculate Levenshtein distance
    len1, len2 = len(text1), len(text2)

    # Initialize the distance matrix
    dp = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]

    # Fill the matrix
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if text1[i - 1] == text2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )

    # Calculate similarity as 1 - normalized distance
    distance = dp[len1][len2]
    max_len = max(len1, len2)
    if max_len == 0:  # Handle empty strings
        return 1.0

    similarity = 1.0 - (distance / max_len)
    return similarity


if __name__ == "__main__":
    print("\n===== Spotify User ID Helper =====")
    print("This utility helps you get your Spotify User ID for use in the migration tool.")
    load_dotenv()
    get_spotify_user_id()
