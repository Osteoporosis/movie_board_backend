from __future__ import annotations

import typing

import fastapi
from firebase_admin import auth, firestore_async  # type: ignore[]

from movie_board_backend.firestore import db
from movie_board_backend.types import (
    IdToken,
    MovieComment,
    MovieCommentId,
    MovieTitle,
    UserId,
)


async def get_uid(id_token: typing.Annotated[IdToken, fastapi.Header()]) -> UserId:
    return UserId(auth.verify_id_token(id_token)["uid"])  # type: ignore[]


async def get_movie_title(title: MovieTitle) -> MovieTitle:
    movie_document = await db.document("movies", title).get()  # type: ignore[]
    if not movie_document.exists:
        raise fastapi.HTTPException(status_code=404, detail=f"unknown {title=}")
    return title


async def get_movie_comment_and_reference(
    title: MovieTitle,
    comment_id: MovieCommentId,
) -> tuple[MovieComment, firestore_async.firestore.AsyncDocumentReference]:
    movie_comment_reference = db.document("movies", title, "comments", comment_id)
    movie_comment_document = await movie_comment_reference.get()  # type: ignore[]
    movie_comment_dict: dict[str, typing.Any] | None = movie_comment_document.to_dict()
    if movie_comment_dict is None:
        raise fastapi.HTTPException(
            status_code=404,
            detail=f"unknown {title=} or {comment_id=}",
        )
    movie_comment = MovieComment(**movie_comment_dict)
    return movie_comment, movie_comment_reference
