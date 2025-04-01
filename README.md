# Telegram to Spotify Music Migration

This project allows you to extract music from a Telegram channel and migrate it to a Spotify playlist.

## Features

- Extract music metadata from a Telegram channel
- Create a new playlist in Spotify
- Search for tracks on Spotify based on titles from Telegram
- Compare track titles using text similarity algorithm (Levenshtein distance)
- Only add tracks that meet a minimum similarity threshold (customizable)
- Add found tracks to the Spotify playlist
- Track progress and report results
- Generate detailed similarity reports

## Prerequisites

- Python 3.7+
- Telegram API credentials (API ID and API Hash)
- Spotify Developer credentials (Client ID, Client Secret, and Redirect URI)
- Spotify User ID

## Setup

1. **Clone the repository**

2. **Install dependencies**

   ```bash
   # Using Poetry
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file with the following details:

   ```
   TELEGRAM_API_ID=your_telegram_api_id
   TELEGRAM_API_HASH=your_telegram_api_hash
   TELEGRAM_CHANNEL_USERNAME=your_channel_username

   # Maximum number of messages to retrieve from Telegram channel
   LIMIT=600

   # Default similarity threshold for track matching (0.0-1.0)
   DEFAULT_SIMILARITY_THRESHOLD=0.5

   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
   SPOTIFY_USER_ID=your_spotify_user_id
   SPOTIFY_PLAYLIST_ID=pl_id_only_if_want_to_add_to_existing_pl
   ```

   - **Telegram API Credentials**: Obtain from [my.telegram.org](https://my.telegram.org)
   - **LIMIT**: Maximum number of messages to retrieve from the Telegram channel (default: 600)
   - **DEFAULT_SIMILARITY_THRESHOLD**: Default similarity threshold for track matching (0.0-1.0, default: 0.5)
   - **Spotify Credentials**: Create a Spotify App at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
   - **Spotify User ID**: Run `python utils.py` to get your Spotify User ID

## Usage

Run the main script to start the migration:

```bash
python main.py
```

The process:

1. The script will check if the music metadata has been previously extracted from Telegram
   - If not, it will connect to Telegram and extract music metadata (requiring authentication)
   - The metadata will be saved to `telegram-musics.json`

2. It will initialize the Spotify client and authenticate
   - If it's your first time, you'll need to authorize the app through your browser

3. You'll be prompted to:
   - Name your Spotify playlist
   - Provide a description for the playlist
   - Set a similarity threshold (0.0-1.0, default: 0.5 or 50%)

4. The script will search for each track on Spotify and match them:
   - Each potential match is compared against the original title using Levenshtein distance
   - Only tracks that meet or exceed the similarity threshold will be added
   - Progress will be displayed during the process, including similarity scores

5. After completion, a summary will show:
   - Total tracks processed
   - Number of tracks successfully added (with similarity ≥ threshold)
   - Number of tracks not found or below the similarity threshold
   - Tracks not found will be saved to `not-found.json`
   - Detailed similarity information will be saved to `similarity_details.json`

## Similarity Matching

The system uses the Levenshtein distance algorithm to compare how similar the Telegram track title is to potential Spotify matches:

- A threshold of 1.0 (100%) means exact matches only
- A threshold of 0.5 (50%) allows for differences (default)
- Lower thresholds allow for more matches but may reduce accuracy

The similarity check helps prevent:
1. Adding incorrect tracks that happen to match search terms
2. Missing tracks due to slight differences in formatting or spelling

## Notes

- The Telegram music metadata extraction may require you to authenticate with your Telegram account
- Spotify search may not find all tracks depending on how well the metadata matches Spotify's database
- You can tune the similarity threshold based on your needs: higher for more precision, lower for more matches
- You can modify the extraction process or search functionality to improve results (I'm open to PRs)
- Last but not least, It's a personal project to help me migrate my music from Telegram to Spotify :)