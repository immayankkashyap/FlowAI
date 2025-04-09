import os
import time
import shutil
import requests
import base64
from dotenv import load_dotenv

# === Load .env file ===
load_dotenv()

# === CONFIGURATION ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = "immayankkashyap"
REPO_NAME = "FlowAI"
NOTES_DIR = "flowai-notes"
SYNCED_DIR = "synced-notes"


def upload_to_github(file_path, file_name):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{file_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": f"Add note {file_name}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }

    response = requests.put(url, json=data, headers=headers)
    return response.status_code == 201 or response.status_code == 200

def sync_notes():
    for filename in os.listdir(NOTES_DIR):
        if filename.endswith(".txt") or filename.endswith(".md"):
            file_path = os.path.join(NOTES_DIR, filename)
            print(f"Syncing {filename}...")
            if upload_to_github(file_path, filename):
                print(f"✅ Synced: {filename}")
                shutil.move(file_path, os.path.join(SYNCED_DIR, filename))
            else:
                print(f"❌ Failed to sync: {filename}")

if __name__ == "__main__":
    print("📡 Watching for new notes...")
    while True:
        sync_notes()
        time.sleep(10)  # Check every 10 seconds
