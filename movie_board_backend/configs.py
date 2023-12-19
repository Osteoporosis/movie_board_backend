from __future__ import annotations

from dotenv import dotenv_values

from .types import UserId

MAX_RESULTS = 10  # for production, set a bigger number
MIN_KEYWORD_LENGTH = 5  # cf. maximum byte is 4 for a mutibyte charactor

TIME_ZONE = "Asia/Seoul"  # need to be internationalization?


ENVS: dict[str, str] = {key: value for key, value in dotenv_values().items() if value}

DOMAIN_NAME = ENVS["DOMAIN_NAME"].removeprefix("https://").removeprefix("http://")
PROJECT_ID = ENVS["PROJECT_ID"]
ADMIN_UID = UserId(ENVS["ADMIN_UID"])
