#!/usr/bin/env python3
import os
import sys
import glob
import requests
from cryptography.fernet import Fernet

def get_symmetric_key(server_url, username, password):
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

def upload_file_to_server(server_url, file_path, username, password):
    url = f"{server_url}/upload-model"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(url, files=files, auth=(username, password))
    response.raise_for_status()
    print(f"Uploaded {file_path} successfully to server.")

def main():
    if len(sys.argv) < 2:
        print("Usage: encrypt_and_upload.py <models_directory>")
        sys.exit(1)
    models_dir = sys.argv[1]

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

if __name__ == "__main__":
    main()
