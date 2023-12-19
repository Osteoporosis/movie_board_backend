from __future__ import annotations

import typing

import fastapi

from movie_board_backend.dependencies import get_movie_title, get_uid  # noqa: TCH001
from movie_board_backend.enums import RouterTags
from movie_board_backend.firestore import db
from movie_board_backend.types import MovieTitle, User, UserId

USERS = RouterTags.USERS
router = fastapi.APIRouter(prefix=f"/{USERS.value}", tags=[USERS])


async def get_user(uid: UserId) -> User:
    user_document = await db.document("users", uid).get()  # type: ignore[]
    user_dict: dict[str, typing.Any] | None = user_document.to_dict()
    user_dict = user_dict or {"uid": uid, "favorites": []}
    return User(**user_dict)


async def set_user(user: User) -> None:
    await db.document("users", user.uid).set(user.model_dump())  # type: ignore[]


@router.get("/me/favorites/")
async def get_user_favorites(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
) -> dict[str, list[MovieTitle]]:
    user = await get_user(uid)
    return {"favorites": user.favorites}


@router.post("/me/favorites/add")
async def add_user_favorite(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, list[MovieTitle]]:
    user = await get_user(uid)
    favorites = set(user.favorites)
    favorites.add(title)
    user.favorites = list(favorites)
    await set_user(user)
    return {"favorites": user.favorites}


@router.post("/me/favorites/{title}/remove")
async def remove_user_favorite(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, list[MovieTitle]]:
    user = await get_user(uid)
    favorites = set(user.favorites)
    favorites.discard(title)
    user.favorites = list(favorites)
    await set_user(user)
    return {"favorites": user.favorites}
