from __future__ import annotations

import typing
from datetime import datetime  # noqa: TCH003

import pydantic

IdToken = str
MovieTitle = str

HtmlContent = str

FixedSizeStr = typing.NewType("FixedSizeStr", str)  # used for document id
UserId = FixedSizeStr
MovieCommentId = FixedSizeStr


class MovieInfo(pydantic.BaseModel):
    released_at: datetime
    is_series: bool
    tags: list[str]
    episodes: list[str]
    image_urls: list[str]
    title: MovieTitle
    description: str
    html_content: HtmlContent


class Movie(pydantic.BaseModel):
    created_at: datetime
    movie_info: MovieInfo


class TimestampedComment(pydantic.BaseModel):
    created_at: datetime
    comment: str


class MovieComment(pydantic.BaseModel):
    author: UserId
    created_at: datetime
    liked_uids: list[UserId]
    comment_histories: list[TimestampedComment]
    title: MovieTitle


class MovieCommentResponse(pydantic.BaseModel):
    comment_id: MovieCommentId
    author: int
    created_at: datetime
    likes: int
    timestamped_comment: TimestampedComment
    title: MovieTitle


class User(pydantic.BaseModel):
    uid: UserId
    favorites: list[MovieTitle]
