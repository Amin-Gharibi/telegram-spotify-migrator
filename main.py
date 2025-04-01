import json
from telegram import Telegram
from spotify import Spotify
from os import getenv, path, remove
from os.path import exists
from dotenv import load_dotenv
from asyncio import run

load_dotenv()
REQUIRED_ENVS = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_CHANNEL_USERNAME',
                 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI', 'SPOTIFY_USER_ID']
MUSIC_DETAILS_FILE = "./telegram-musics.json"
# Load LIMIT from .env or use default value if not defined
LIMIT = int(getenv('LIMIT', 100))
NOT_FOUND_FILE = "./not-found.json"
# Load DEFAULT_SIMILARITY_THRESHOLD from .env or use default value if not defined
DEFAULT_SIMILARITY_THRESHOLD = float(getenv('DEFAULT_SIMILARITY_THRESHOLD', 0.5))
CACHE_FILE = ".cache"


async def main():
    # Check for required environment variables
    for env in REQUIRED_ENVS:
        if getenv(env) is None:
            raise EnvironmentError(f"{env} is not set!")
    
    # Remove .cache file if it exists (we're using session_tokens.json instead)
    if path.exists(CACHE_FILE):
        print(f"Removing {CACHE_FILE} file (using session_tokens.json instead)...")
        remove(CACHE_FILE)

    # Step 1: Get music details from Telegram or load from file
    if exists(MUSIC_DETAILS_FILE):
        print("Music details file exists! Skipping extracting musics...")
        with open(MUSIC_DETAILS_FILE, "r") as f:
            music_titles = json.loads(f.read())
    else:
        print("\n===== Step 1: Extracting Musics From Telegram =====")
        print(f"Using message limit: {LIMIT} (configurable in .env file)")
        tel = Telegram(getenv("TELEGRAM_API_ID"), getenv("TELEGRAM_API_HASH"), getenv("TELEGRAM_CHANNEL_USERNAME"))
        await tel.init_conn(True)
        musics = await tel.get_music_files(limit=LIMIT)
        music_titles = list(map(lambda m: m["title"] + " - " + m["performer"], musics))
        with open(MUSIC_DETAILS_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(music_titles))
        print(f"Music details written to {MUSIC_DETAILS_FILE}")

    # Step 2: Initialize Spotify
    print("\n===== Step 2: Initializing Spotify =====")
    spotify = Spotify(getenv("SPOTIFY_CLIENT_ID"), getenv("SPOTIFY_CLIENT_SECRET"), getenv("SPOTIFY_REDIRECT_URI"),
                      getenv("SPOTIFY_USER_ID"))

    # Step 3: Configure Playlist
    print("\n===== Step 3: Configure Playlist =====")
    playlist_id = getenv("SPOTIFY_PLAYLIST_ID")
    playlist_name = None
    playlist_description = None
    if not playlist_id:
        # Ask for playlist name and other parameters
        playlist_name = input("Enter a name for your Spotify playlist [Telegram Music]: ") or "Telegram Music"
        playlist_description = input("Enter the description for your Spotify playlist [Imported from Telegram]: ") or "Imported from Telegram"
        print(f"Playlist name: {playlist_name}")
        print(f"Playlist description: {playlist_description}")
    else:
        print("Using Playlist ID provided in environment variables.")

    # Step 4: Configure similarity threshold
    print("\n===== Step 4: Configure Similarity Threshold =====")
    similarity_input = input(f"Enter similarity threshold (0.0-1.0) [{DEFAULT_SIMILARITY_THRESHOLD}]: ")
    try:
        similarity_threshold = float(similarity_input) if similarity_input else DEFAULT_SIMILARITY_THRESHOLD
        # Validate the threshold is between 0 and 1
        if similarity_threshold < 0 or similarity_threshold > 1:
            print(f"Invalid threshold! Using default: {DEFAULT_SIMILARITY_THRESHOLD}")
            similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
    except ValueError:
        print(f"Invalid threshold format! Using default: {DEFAULT_SIMILARITY_THRESHOLD}")
        similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
    print(f"Using similarity threshold: {similarity_threshold * 100:.1f}%")

    # Step 5: Migrate tracks from Telegram to Spotify
    print(f"\n===== Step 5: Migrating Tracks ({len(music_titles)}) =====")
    result = spotify.migrate_tracks(music_titles, playlist_name, playlist_description, playlist_id, similarity_threshold)

    # Step 6: Print summary
    print("\n===== Migration Summary =====")
    print(f"Playlist: {playlist_name or playlist_id}")
    print(f"Total tracks: {len(music_titles)}")
    print(f"Message limit used: {LIMIT}")
    print(f"Successfully added: {result['found_tracks']} (similarity ≥ {similarity_threshold * 100:.1f}%)")
    print(f"Not found or below similarity threshold: {result['not_found_tracks']}")

    # Optionally save not found tracks to a file
    if result['not_found_tracks'] > 0:
        with open(NOT_FOUND_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(result['not_found_list'], indent=2))
        print(f"List of tracks not found saved to {NOT_FOUND_FILE}")
    
    # Mention similarity details
    print(f"Detailed similarity information saved to similarity_details.json")


if __name__ == '__main__':
    run(main())
