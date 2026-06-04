# appdata/config/whats_new.py
"""
Configuration for Instanciar's live What's New panel.

Live source of truth:
    GitHub repository folder:
        https://github.com/officialjivaro/Instanciar/tree/main/release_notes

Exact file to create manually inside that folder:
    release_notes/instanciar_whats_new.md

The app does NOT use bundled release notes. It reads the raw GitHub Markdown
file so you can update the panel without requiring users to redownload the app.
"""

GITHUB_REPO_URL = "https://github.com/officialjivaro/Instanciar"
GITHUB_BRANCH = "main"
GITHUB_RELEASE_NOTES_FOLDER = "release_notes"
GITHUB_LIVE_FILE_NAME = "instanciar_whats_new.md"

GITHUB_RELEASE_NOTES_FOLDER_URL = (
    f"{GITHUB_REPO_URL}/tree/{GITHUB_BRANCH}/{GITHUB_RELEASE_NOTES_FOLDER}"
)

GITHUB_LIVE_FILE_PATH = f"{GITHUB_RELEASE_NOTES_FOLDER}/{GITHUB_LIVE_FILE_NAME}"

WHATS_NEW_URL = (
    "https://raw.githubusercontent.com/officialjivaro/Instanciar/"
    f"{GITHUB_BRANCH}/{GITHUB_LIVE_FILE_PATH}"
)

WHATS_NEW_RELEASE_NOTES_URL = (
    f"{GITHUB_REPO_URL}/blob/{GITHUB_BRANCH}/{GITHUB_LIVE_FILE_PATH}"
)

WHATS_NEW_TIMEOUT_SECONDS = 4

INSTANCIAR_DOWNLOAD_URL = "https://www.jivaro.net/content/programs/instanciar"
