from __future__ import annotations

import contextlib
import typing

import fastapi
from firebase_admin import firestore_async  # type: ignore[]
from google.api_core import exceptions

from movie_board_backend.configs import ADMIN_UID, MAX_RESULTS, MIN_KEYWORD_LENGTH
from movie_board_backend.dependencies import (
    get_movie_comment_and_reference,
    get_movie_title,
    get_uid,
)
from movie_board_backend.enums import RouterTags
from movie_board_backend.firestore import db
from movie_board_backend.time_utils import get_now
from movie_board_backend.types import (
    Movie,
    MovieComment,
    MovieCommentId,
    MovieCommentResponse,
    MovieInfo,
    MovieTitle,
    TimestampedComment,
    UserId,
)

MOVIES = RouterTags.MOVIES
router = fastapi.APIRouter(prefix=f"/{MOVIES.value}", tags=[MOVIES])


ResultLimit = typing.Annotated[int, fastapi.Query(ge=1, le=MAX_RESULTS)]


@router.get("/")
async def get_movies(
    last_title: MovieTitle | None = None,
    limit: ResultLimit = MAX_RESULTS,
) -> list[dict[str, typing.Any]]:
    movies_reference = db.collection("movies")
    start_movie_document = await movies_reference.document(
        last_title,  # type: ignore[]
    ).get()
    query = movies_reference.order_by(  # type: ignore[]
        field_path="created_at",
        direction=firestore_async.firestore.Query.DESCENDING,
    )
    if start_movie_document.exists:
        query = query.start_after(  # type: ignore[]
            {"created_at": start_movie_document.get("created_at")},
        )
    return [
        movie_document.to_dict()  # type: ignore[]
        for movie_document in await query.limit(limit).get()  # type: ignore[]
    ]


@router.post("/add")
async def add_movie(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    movie_info: MovieInfo,
) -> dict[str, str]:
    """
    Add a Movie to the DB

    Notes:
    - Only the ADMIN_UID defined in `.env` can add a Movie.
    - Restart this app after adding a Movie is highly recommended as the dependency
      `get_movie_title` uses cache.
    """
    if uid != ADMIN_UID:
        raise fastapi.HTTPException(status_code=403)
    movie = Movie(created_at=get_now(), movie_info=movie_info)
    movie_reference = db.collection("movies").document(movie_info.title)
    await movie_reference.create(movie.model_dump())  # type: ignore[]
    return {"message": "done"}


@router.get("/{title}/")
async def get_movie_by_title(title: MovieTitle) -> dict[str, typing.Any] | None:
    movie_document = await db.document("movies", title).get()  # type: ignore[]
    return movie_document.to_dict()


@router.get("/search/{keyword}/", dependencies=[fastapi.Depends(get_uid)])
async def search_movies(
    keyword: str,
    limit: ResultLimit = MAX_RESULTS,
) -> dict[str, list[dict[str, typing.Any]]]:
    keyword = keyword.strip()
    if len(keyword.encode("utf-8")) < MIN_KEYWORD_LENGTH:
        raise fastapi.HTTPException(status_code=400, detail="The keyword is too short.")
    movies: list[Movie] = []
    async for movie_document in db.collection("movies").stream():  # type: ignore[]
        if len(movies) > limit:
            break
        movie_dict: dict[str, typing.Any] | None = movie_document.to_dict()
        if movie_dict is None:
            continue
        movie = Movie.model_validate(movie_dict)
        movie_info = movie.movie_info
        if keyword in movie_info.title or keyword in movie_info.tags:
            movies.append(movie)
    return {"movies": [movie.model_dump() for movie in movies]}


# XXX: do not use this in production.
# consider a dedicated process for regular caching or apscheduler.
@router.get("/top10")
async def get_movie_top10() -> list[tuple[int, MovieTitle]]:
    date = str(get_now().date())
    results: list[tuple[int, MovieTitle]] = []
    async for movie_document in db.collection("movies").stream():  # type: ignore[]
        title = MovieTitle(movie_document.get("movie_info.title"))
        counter_document = (
            await db.collection("movies", title, "daily_counters")
            .document(date)
            .get()  # type: ignore[]
        )
        counter = typing.cast(int | None, counter_document.get("counter"))
        if counter:
            results.append((counter, title))
    return sorted(results, reverse=True)[:10]


@router.post("/{title}/increase_counter")
async def increase_movie_counter(
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, str]:
    date = str(get_now().date())
    counter_reference = db.collection("movies", title, "daily_counters").document(date)
    with contextlib.suppress(exceptions.AlreadyExists):
        await counter_reference.create({"counter": 0})  # type: ignore[]
    await counter_reference.update(  # type: ignore[]
        {"counter": firestore_async.firestore.Increment(1)},
    )
    return {"message": "done"}


async def set_like_document(
    title: MovieTitle,
    uid: UserId,
    data: dict[str, bool],
) -> None:
    like_document_reference = db.collection("movies", title, "likes").document(uid)
    await like_document_reference.set(data)  # type: ignore[]


@router.put("/{title}/likes/unlike")
async def unlike_movie(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, str]:
    await set_like_document(title, uid, {"is_valid": False})
    return {"message": "done"}


@router.post("/{title}/likes/like")
async def like_movie(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, str]:
    await set_like_document(title, uid, {"is_valid": True})
    return {"message": "done"}


@router.get("/{title}/likes/count")
async def get_movie_likes(
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, int]:
    likes_reference = db.collection("movies", title, "likes")
    query = likes_reference.where(  # type: ignore[]
        field_path="is_valid",
        op_string="==",
        value=True,
    )
    results = await query.count().get()  # type: ignore[]
    count = int(results[0][0].value)  # type: ignore[]
    return {"likes": count}


# XXX: we don't have the nickname system. using hashed uids instead.
@router.get("/{title}/comments/")
async def get_movie_comments(
    title: MovieTitle,
    last_comment_id: MovieCommentId | None = None,
    limit: ResultLimit = MAX_RESULTS,
) -> list[MovieCommentResponse]:
    movie_comments_reference = db.collection("movies", title, "comments")
    start_movie_comment_document = await movie_comments_reference.document(
        last_comment_id,  # type: ignore[]
    ).get()
    query = movie_comments_reference.order_by(  # type: ignore[]
        field_path="created_at",
        direction=firestore_async.firestore.Query.DESCENDING,
    )
    if start_movie_comment_document.exists:
        query = query.start_after(  # type: ignore[]
            {"created_at": start_movie_comment_document.get("created_at")},
        )
    movie_comments: list[tuple[MovieCommentId, MovieComment]] = [
        (comment_document.id, MovieComment(**comment_document.to_dict()))  # type: ignore[]
        for comment_document in await query.limit(limit).get()  # type: ignore[]
    ]
    return [
        MovieCommentResponse(
            comment_id=comment_id,
            author=hash(movie_comment.author),
            created_at=movie_comment.created_at,
            likes=len(movie_comment.liked_uids),
            timestamped_comment=movie_comment.comment_histories.pop(),
            title=movie_comment.title,
        )
        for comment_id, movie_comment in movie_comments
    ]


@router.get("/{title}/comments/count")
async def get_movie_comments_count(
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
) -> dict[str, int]:
    comments_reference = db.collection("movies", title, "comments")
    results = await comments_reference.count().get()  # type: ignore[]
    count = int(results[0][0].value)  # type: ignore[]
    return {"comments": count}


@router.post("/{title}/comments/add")
async def add_movie_comment(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    title: typing.Annotated[MovieTitle, fastapi.Depends(get_movie_title)],
    comment: str,
) -> dict[str, str]:
    now = get_now()
    movie_comment = MovieComment(
        author=uid,
        created_at=now,
        liked_uids=[],
        comment_histories=[TimestampedComment(created_at=now, comment=comment)],
        title=title,
    )
    await db.collection("movies", title, "comments").add(  # type: ignore[]
        movie_comment.model_dump(),
    )
    return {"done_at": str(now)}


@router.put("/{title}/comments/{comment_id}/edit")
async def append_movie_comment(  # actually append instead of edit
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    movie_comment_and_reference: typing.Annotated[
        tuple[MovieComment, firestore_async.firestore.AsyncDocumentReference],
        fastapi.Depends(get_movie_comment_and_reference, use_cache=False),
    ],
    comment: str,
) -> dict[str, str]:
    movie_comment, movie_comment_reference = movie_comment_and_reference
    comment_histories = movie_comment.comment_histories
    if (movie_comment.author != uid) or (
        comment_histories and comment_histories[-1].comment == comment
    ):
        raise fastapi.HTTPException(status_code=400, detail="rejected")
    now = get_now()
    comment_histories.append(TimestampedComment(created_at=now, comment=comment))
    new_movie_comment_dict = movie_comment.model_dump()
    await movie_comment_reference.update(  # type: ignore[]
        {"comment_histories": new_movie_comment_dict["comment_histories"]},
    )
    return {"done_at": str(now)}


@router.put("/{title}/comments/{comment_id}/likes/unlike")
async def unlike_movie_comment(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    movie_comment_and_reference: typing.Annotated[
        tuple[MovieComment, firestore_async.firestore.AsyncDocumentReference],
        fastapi.Depends(get_movie_comment_and_reference, use_cache=False),
    ],
) -> dict[str, int]:
    movie_comment, movie_comment_reference = movie_comment_and_reference
    liked_uids = set(movie_comment.liked_uids)
    liked_uids.discard(uid)
    movie_comment.liked_uids = list(liked_uids)
    await movie_comment_reference.update(  # type: ignore[]
        {"liked_uids": movie_comment.liked_uids},
    )
    return {"likes": len(movie_comment.liked_uids)}


@router.put("/{title}/comments/{comment_id}/likes/like")
async def like_movie_comment(
    uid: typing.Annotated[UserId, fastapi.Depends(get_uid)],
    movie_comment_and_reference: typing.Annotated[
        tuple[MovieComment, firestore_async.firestore.AsyncDocumentReference],
        fastapi.Depends(get_movie_comment_and_reference, use_cache=False),
    ],
) -> dict[str, int]:
    movie_comment, movie_comment_reference = movie_comment_and_reference
    liked_uids = set(movie_comment.liked_uids)
    liked_uids.add(uid)
    movie_comment.liked_uids = list(liked_uids)
    await movie_comment_reference.update(  # type: ignore[]
        {"liked_uids": movie_comment.liked_uids},
    )
    return {"likes": len(movie_comment.liked_uids)}
