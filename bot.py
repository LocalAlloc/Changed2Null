import optparse
import colorama
import discord
import asyncio
import sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
import base64
from cryptography.hazmat.primitives import hashes
from colorama import Fore, Style, init
init(autoreset=True)

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# ID of the channel you want to read messages from
CHANNEL_ID = CHANNEL_ID
def hash_with_sha256(data):
    """
    Hash the provided data using SHA-256.
    :param data: Data to hash (bytes or str)
    :return: SHA-256 hash (bytes)
    """
    if isinstance(data, str):
        data = data.encode('utf-8')  # Convert string to bytes
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data)
    return digest.finalize()


def encrypt_message(key, message):
    key = hash_with_sha256(key)  # Hash key with SHA-256
    print(colorama.Fore.GREEN + "Hashed Key (Alpha):", key.hex())

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()

    iv = os.urandom(16)
    print(colorama.Fore.BLUE + "Generated IV (Alpha):", iv.hex())

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_message = base64.b64encode(iv + ciphertext).decode()
    print(colorama.Fore.LIGHTCYAN_EX + "Ciphertext (Alpha):", encrypted_message)

    return encrypted_message

def decrypt_message(key, encrypted_message):
    try:
        key = hash_with_sha256(key)  # Hash key with SHA-256
        print(colorama.Fore.GREEN + "Hashed Key (Responder):", key.hex())

        encrypted_data = base64.b64decode(encrypted_message)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        print(colorama.Fore.BLUE + "Extracted IV (Responder):", iv.hex())
        print(colorama.Fore.LIGHTCYAN_EX + "Ciphertext (Responder):", ciphertext.hex())

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode()
    except Exception as e:
        raise ValueError(colorama.Fore.RED + f"Decryption error: {e}")

def prepare_key(base64_key):
    # Decode Base64 key and hash it with SHA-256
    raw_key = base64.b64decode(base64_key)
    hashed_key = hash_with_sha256(raw_key)
    print(colorama.Fore.GREEN + "Base64 Key:", base64_key)
    print(colorama.Fore.LIGHTGREEN_EX + "Raw Key (decoded):", raw_key.hex())
    print(colorama.Fore.MAGENTA + "Hashed Key:", hashed_key.hex())
    return hashed_key

class MyClient(discord.Client):
    def __init__(self, intents, aes_key):
        super().__init__(intents=intents)
        self.channel = None
        self.new_messages = []
        self.new_message_event = asyncio.Event()
        self.aes_key = aes_key  # Store the provided AES key

    async def on_ready(self):
        print(colorama.Fore.BLACK + f'Logged in as {self.user}')
        self.channel = self.get_channel(CHANNEL_ID)
        if self.channel is not None:
            print(colorama.Fore.GREEN + f'Connected to channel: {self.channel.name}')
            asyncio.create_task(self.display_new_messages())
            asyncio.create_task(self.message_input_loop())
        else:
            print(colorama.Fore.RED + "Channel not found.")

    async def send_message(self, content):
        encrypted_content = encrypt_message(self.aes_key, content)
        if self.channel:
            await self.channel.send(encrypted_content)
            print(colorama.Fore.GREEN + f"Sent encrypted message: {encrypted_content}")
        else:
            print(colorama.Fore.RED + "Channel not available to send messages.")

    async def display_new_messages(self):
        while True:
            await self.new_message_event.wait()
            self.new_message_event.clear()
            while self.new_messages:
                message = self.new_messages.pop(0)
                self.clear_input_line()
                try:
                    decrypted_content = decrypt_message(self.aes_key, message.content)
                    print(colorama.Fore.GREEN + f'New decrypted message from {message.author}: {decrypted_content}')
                except Exception as e:
                    print(colorama.Fore.RED + f'New message from {message.author} (undecipherable): {message.content}')
                    print(colorama.Fore.RED + f"Decryption error: {e}")
                self.restore_input_line()

    async def message_input_loop(self):
        while True:
            message_to_send = await self.get_user_input(colorama.Fore.LIGHTCYAN_EX + "Message you want to send: ")
            if message_to_send.strip():
                await self.send_message(message_to_send)

    async def get_user_input(self, prompt):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)

    def clear_input_line(self):
        sys.stdout.write("\033[K")
        sys.stdout.write("\r")
        sys.stdout.flush()

    def restore_input_line(self):
        sys.stdout.write(colorama.Fore.LIGHTCYAN_EX + "Message you want to send: ")
        sys.stdout.flush()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.channel.id == CHANNEL_ID:
            self.new_messages.append(message)
            self.new_message_event.set()


if __name__ == "__main__":
    parser = optparse.OptionParser('Usage: %prog -k <AES Key, that was generated by the Alpha.>')
    parser.add_option('-k', dest='AES_key', type="string", help="Enter the Base64-encoded AES Key.")
    (options, args) = parser.parse_args()

    if not options.AES_key:
        print(colorama.Fore.RED + "Error: AES key is required. Use the -k option to provide it.")
        sys.exit(0)

    try:
        #key = base64.b64decode(options.AES_key)
        key = prepare_key(options.AES_key)
        if len(key) not in (16, 24, 32):
            raise ValueError(colorama.Fore.RED + "Invalid AES key length. It must be 16, 24, or 32 bytes.")
    except Exception as e:
        print(colorama.Fore.Red + f"Error: Invalid AES Key provided. {e}")
        sys.exit(0)

    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents, aes_key=key)  
    client.run(TOKEN)
