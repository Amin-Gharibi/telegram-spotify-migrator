import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename, MessageMediaDocument


class Telegram:
    def __init__(self, api_id, api_hash, channel_username):
        print("\n===== Telegram Authentication =====")
        # try to load previous connection
        telegram_token = self.load_session()

        self.session_string = StringSession(telegram_token)
        self.client = TelegramClient(self.session_string, api_id, api_hash)
        self.channel_username = channel_username

    async def init_conn(self, save_session: bool = False) -> None:
        print("Initializing Telegram Connection...")
        await self.client.start(phone=lambda: input("Enter your phone number: "),
                                password=lambda: input("Enter your 2FA-Password [leave empty if none]: ") or None,
                                code_callback=lambda: input("Enter the verification code sent to you: "))
        print("Connection Initialized Successfully.")
        if save_session:
            self.save_session()

    async def get_music_files(self, limit: int = 100):
        print(f"\n===== Retrieving Music Files (Limit: {limit}) =====")
        # Make sure we're connected
        if not self.client.is_connected():
            await self.client.connect()
            
        # Get the channel entity
        print(f"Getting channel: {self.channel_username}")
        channel = await self.client.get_entity(self.channel_username)
        
        # Retrieve messages from the channel
        print(f"Retrieving messages (limit: {limit})...")
        messages = await self.client.get_messages(channel, limit=limit)

        music_files = []  # List to store the music files
        process_count = 0

        for msg in messages:
            process_count += 1
            if process_count % 50 == 0:
                print(f"Progress: {process_count}/{len(messages)} messages processed")
                
            # Check if the message contains media
            if msg.media and isinstance(msg.media, MessageMediaDocument):
                document = msg.media.document
                # Check if the document is not null
                if document:
                    # Check if the document attributes indicate it's audio
                    is_audio = any(attr for attr in document.attributes if isinstance(attr, DocumentAttributeAudio))

                    if is_audio:
                        # Initialize default values
                        title = 'Unknown'
                        performer = 'Unknown'
                        filename = 'unknown.mp3'

                        # Extract audio attributes
                        audio_attr = next(
                            (attr for attr in document.attributes if isinstance(attr, DocumentAttributeAudio)), None)
                        if audio_attr:
                            title = audio_attr.title or 'Unknown'
                            performer = audio_attr.performer or 'Unknown'

                        # Extract filename attribute
                        filename_attr = next(
                            (attr for attr in document.attributes if isinstance(attr, DocumentAttributeFilename)), None)
                        if filename_attr:
                            filename = filename_attr.file_name or 'unknown.mp3'

                        # Append to music files
                        music_files.append({
                            "id": msg.id,
                            "title": title,
                            "performer": performer,
                            "filename": filename,
                            "file_size": document.size,
                            "mime_type": document.mime_type,
                            "date": msg.date,
                            "document": document
                        })

        print(f"Found {len(music_files)} music files in the channel.")
        return music_files

    @staticmethod
    def load_session():
        print("Loading Previous Sessions If Available...")
        try:
            with open("./session_tokens.json", "r") as session_file:
                tokens = json.loads(session_file.read())
                if "telegram" not in tokens:
                    raise SyntaxError("Telegram token not found")
                elif not tokens["telegram"]:
                    print("No Previous Sessions Found.")
                return tokens["telegram"] or ''
        except FileNotFoundError:
            print("No saved session found, will create a new one")
            return ''
        except SyntaxError as e:
            print("Syntax Error Occurred: ", e)
            return ''
        except Exception as e:
            print("An unknown error occurred while attempting to load the saved session:", e)
            return ''

    def save_session(self):
        session_string = self.session_string.save()
        try:
            with open("./session_tokens.json", "r") as session_file:
                tokens = json.loads(session_file.read())
                if "telegram" not in tokens:
                    tokens = {"telegram": "", "spotify": ""}
        except FileNotFoundError:
            print("No saved session found, will create a new one")
            tokens = {"telegram": "", "spotify": ""}
        except SyntaxError as e:
            print("Syntax Error Occurred: ", e)
            return
        except Exception as e:
            print("An unknown error occurred while attempting to load the saved session:", e)
            return

        tokens["telegram"] = session_string
        with open("./session_tokens.json", "w") as session_file:
            session_file.write(json.dumps(tokens))
        print("Session Saved Successfully!")
