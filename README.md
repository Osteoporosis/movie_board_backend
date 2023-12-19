# Movie Board Backend
using Firebase

## How to run
- Get an Ubuntu compatible Linux box or wsl.
- Clone the github repository to proper path and change to the directory.
- Start a Firebase project from https://console.firebase.google.com
- Get `serviceAccountKey.json` from 'service accounts' under 'project settings' and confirm fields with `serviceAccountKey_template.json`.
- Navigate to the IAM console from the link under 'all service accounts', then add the `Cloud Firestore Editor` role to the service account.
- Fill the `.env` file except FIREBASE_WEB_API_KEY, ADMIN_EMAIL and ADMIN_PASSWORD(used only for `scripts/get_id_token.py`). Use `.env_template`.
- `$ source init.sh` to install libraries.
- `$ source dev.sh` to run the server.

## Recommended VSCode extensions
- Python
- Black Formatter
- Ruff

