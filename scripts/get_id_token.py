from __future__ import annotations

import json
import typing
import urllib.request
from pprint import pprint

from dotenv import dotenv_values

CONFIG: dict[str, str | None] = dotenv_values()
FIREBASE_WEB_API_KEY = CONFIG.get("FIREBASE_WEB_API_KEY") or ""
ADMIN_EMAIL = CONFIG.get("ADMIN_EMAIL") or ""
ADMIN_PASSWORD = CONFIG.get("ADMIN_PASSWORD") or ""


def login(
    email: str,
    password: str,
    firebase_web_api_key: str,
) -> typing.Any:  # noqa: ANN401
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
        + firebase_web_api_key
    )

    data: dict[str, str | bool] = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    data_json = json.dumps(data).encode("utf-8")

    headers: dict[str, str] = {"Content-Type": "application/json"}

    request = urllib.request.Request(url, data_json, headers)  # noqa: S310
    with urllib.request.urlopen(request) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    pprint(login(ADMIN_EMAIL, ADMIN_PASSWORD, FIREBASE_WEB_API_KEY))  # noqa: T203


if __name__ == "__main__":
    main()
