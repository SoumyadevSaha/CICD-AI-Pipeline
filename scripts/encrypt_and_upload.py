#!/usr/bin/env python3
import os
import sys
import glob
import requests
from cryptography.fernet import Fernet

def get_symmetric_key(server_url, username, password):
    # Remove any extraneous whitespace from the URL
    server_url = server_url.strip()
    response = requests.get(f"{server_url}/get-key", auth=(username, password))
    response.raise_for_status()
    key = response.json().get("key")
    if not key:
        raise Exception("No key received from server")
    return key

def encrypt_file(file_path, key):
    fernet = Fernet(key.encode())
    with open(file_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    enc_file_path = file_path + ".enc"
    with open(enc_file_path, "wb") as f:
        f.write(encrypted)
    return enc_file_path

def decrypt_file(file_path, key):
    fernet = Fernet(key.encode())
    with open(file_path, "rb") as f:
        data = f.read()
    decrypted = fernet.decrypt(data)
    dec_file_path = file_path.replace(".enc", ".dec")
    with open(dec_file_path, "wb") as f:
        f.write(decrypted)
    return dec_file_path

def upload_file_to_server(server_url, file_path, username, password):
    url = f"{server_url}/upload-model"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(url, files=files, auth=(username, password))
    response.raise_for_status()
    print(f"Uploaded {file_path} successfully to server.")

def upload_mode(models_dir):
    username = os.environ.get("SERVER_USERNAME")
    password = os.environ.get("SERVER_PASSWORD")
    server_url = os.environ.get("SERVER_URL")
    if not all([username, password, server_url]):
        print("Missing one or more required environment variables: SERVER_USERNAME, SERVER_PASSWORD, SERVER_URL")
        sys.exit(1)

    print("Requesting symmetric key from server...")
    key = get_symmetric_key(server_url, username, password)
    print("Received symmetric key.")

    model_files = glob.glob(os.path.join(models_dir, "*.h5")) + glob.glob(os.path.join(models_dir, "*.keras"))
    if not model_files:
        print("No model files found.")
        sys.exit(0)

    for file in model_files:
        print(f"Processing model file: {file}")
        enc_file = encrypt_file(file, key)
        print(f"Encrypted file saved as: {enc_file}")
        print("Uploading encrypted file to server...")
        upload_file_to_server(server_url, enc_file, username, password)

def decrypt_mode(file_path):
    key = os.environ.get("SERVER_KEY")
    if not key:
        print("Missing required environment variable: SERVER_KEY")
        sys.exit(1)
    print(f"Decrypting {file_path}...")
    dec_file = decrypt_file(file_path, key)
    print(f"Decrypted file saved as: {dec_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  To upload (encrypt and upload files): encrypt_and_decrypt.py upload <models_directory>")
        print("  To decrypt a file: encrypt_and_decrypt.py decrypt <encrypted_file>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "upload":
        models_dir = sys.argv[2]
        upload_mode(models_dir)
    elif mode == "decrypt":
        file_path = sys.argv[2]
        decrypt_mode(file_path)
    else:
        print("Invalid mode. Use 'upload' or 'decrypt'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
