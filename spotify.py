import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils import calculate_similarity


class Spotify:
    def __init__(self, client_id, client_secret, redirect_uri, user_id):
        print("\n===== Spotify Authentication =====")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.user_id = user_id

        # load previous sessions or create a new one
        print("Loading Previous Spotify Session If Available...")
        self.tokens = self.load_tokens()
        self.spotify = None
        self.auth_manager = None
        self.initialize_client()

    def initialize_client(self):
        scopes = [
            "playlist-modify-private",
            "playlist-modify-public",
            "user-read-private",
            "user-library-read"
        ]

        # Create auth manager without cache
        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=" ".join(scopes),
            cache_path=None,  # Don't use cache file
            open_browser=False
        )
        
        # Check if we have a valid token in session_tokens.json
        if self.tokens and "spotify" in self.tokens and self.tokens["spotify"]:
            print("Using token from session_tokens.json")
            token_info = self.auth_manager.refresh_access_token(self.tokens.get("spotify_refresh", "")) if "spotify_refresh" in self.tokens else None
            
            if token_info:
                # If refresh worked, use the new token
                print("Refreshed Spotify token successfully")
                self.save_token_info(token_info)
                self.spotify = spotipy.Spotify(auth=token_info["access_token"])
            else:
                # Try to use the access token directly
                print("Using existing access token")
                self.spotify = spotipy.Spotify(auth=self.tokens["spotify"])
        else:
            # No token available, need to get a new one
            print("No cached token found, initializing new Spotify authentication...")
            auth_url = self.auth_manager.get_authorize_url()
            print("\n===== Spotify Authorization =====")
            print("1. Open this URL in your browser and log in:")
            print(auth_url)
            print("2. After logging in, you will be redirected.")
            redirected_url = input("3. Paste the redirected URL here: ")
            
            # Get new token from redirect URL
            code = self.auth_manager.parse_response_code(redirected_url)
            if code:
                token_info = self.auth_manager.get_access_token(code)
                self.save_token_info(token_info)
                self.spotify = spotipy.Spotify(auth=token_info["access_token"])
                print("New Spotify token obtained and saved")
            else:
                print("Failed to obtain Spotify token")

    def create_playlist(self, name, description):
        print(f"\n===== Creating Spotify Playlist =====")
        if not self.spotify:
            raise Exception("Spotify client not initialized")

        print(f"Creating playlist: '{name}' with description: '{description}'")
        playlist = self.spotify.user_playlist_create(
            user=self.user_id,
            name=name,
            public=False,
            description=description
        )

        print(f"Created playlist: {name} (ID: {playlist['id']})")
        return playlist['id']

    def search_track(self, query, similarity_threshold=0.5, limit=5):
        if not self.spotify:
            raise Exception("Spotify client not initialized")

        # Search for multiple tracks to increase the chance of finding a good match
        results = self.spotify.search(q=query, type="track", limit=limit)
        
        best_match = None
        best_similarity = 0
        
        if results['tracks']['items']:
            # Check each result for similarity with the query
            for track in results['tracks']['items']:
                # Construct a comparable string from the track data
                track_title = track['name']
                track_artist = track['artists'][0]['name']
                track_full = f"{track_title} - {track_artist}"
                
                # Calculate similarity
                similarity = calculate_similarity(query, track_full)
                
                # Update best match if this is better
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'id': track['id'],
                        'name': track_title,
                        'artist': track_artist,
                        'uri': track['uri'],
                        'similarity': similarity
                    }
            
            # Only return if the best match is above the threshold
            if best_match and best_similarity >= similarity_threshold:
                return best_match
                
        return None

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        print(f"\n===== Adding Tracks to Playlist =====")
        if not self.spotify:
            raise Exception("Spotify client not initialized")

        total_tracks = len(track_uris)
        print(f"Adding {total_tracks} tracks to playlist...")
        
        # Split into batches of 100 (Spotify API limit)
        batch_count = 0
        for i in range(0, total_tracks, 100):
            batch_count += 1
            batch = track_uris[i:i + 100]
            batch_size = len(batch)
            print(f"Processing batch {batch_count}: Adding {batch_size} tracks ({i+1}-{min(i+batch_size, total_tracks)} of {total_tracks})")
            self.spotify.playlist_add_items(playlist_id, batch)

        print(f"Successfully added {total_tracks} tracks to playlist")

    def migrate_tracks(self, track_titles, playlist_name="Telegram Music",
                       playlist_description="Imported from Telegram", playlist_id=None, similarity_threshold=0.9):
        # Create a new playlist if no ID provided
        if not playlist_id:
            playlist_id = self.create_playlist(playlist_name, playlist_description)
        else:
            print(f"\n===== Using Existing Playlist =====")
            print(f"Using existing playlist with ID: {playlist_id}")

        # Search for each track and collect URIs
        track_uris = []
        not_found = []
        similarity_details = []  # For storing similarity scores

        print(f"\n===== Searching for Tracks =====")
        print(f"Searching for {len(track_titles)} tracks on Spotify...")
        print(f"Using similarity threshold of {similarity_threshold * 100}%")

        for i, title in enumerate(track_titles):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(track_titles)} tracks processed ({(i/len(track_titles)*100):.1f}%)")

            track = self.search_track(title, similarity_threshold)
            if track:
                track_uris.append(track['uri'])
                similarity_details.append({
                    'telegram_title': title,
                    'spotify_title': f"{track['name']} - {track['artist']}",
                    'similarity': track['similarity']
                })
                print(f"Found: {title} → {track['name']} by {track['artist']} (Similarity: {track['similarity']:.2f})")
            else:
                not_found.append(title)
                print(f"Not found with enough similarity: {title}")

        # Add found tracks to the playlist
        if track_uris:
            self.add_tracks_to_playlist(playlist_id, track_uris)

        # Save similarity details to a file
        print(f"\n===== Saving Similarity Details =====")
        with open("similarity_details.json", "w", encoding="utf-8") as f:
            json.dump(similarity_details, f, indent=2, ensure_ascii=False)
        print(f"Similarity details saved to similarity_details.json")

        return {
            "playlist_id": playlist_id,
            "found_tracks": len(track_uris),
            "not_found_tracks": len(not_found),
            "not_found_list": not_found,
            "similarity_details": similarity_details
        }

    def load_tokens(self):
        """Load all stored tokens from session_tokens.json"""
        try:
            with open("./session_tokens.json", "r") as session_file:
                return json.loads(session_file.read())
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return {}

    def save_token_info(self, token_info):
        """Save both access and refresh tokens to session_tokens.json"""
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
