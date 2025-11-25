import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema


router = APIRouter()

# Write your code here


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = math.ceil(total_items / per_page)
    if page > 1:
        prev_page = build_url(request, page - 1, per_page)
        start = (page - 1) * per_page
    elif page == 1:
        prev_page = None
        start = 0
    else:
        raise HTTPException(status_code=404, detail="Page not found")
    if page < total_pages:
        next_page = build_url(request, page + 1, per_page)
    elif page == total_pages:
        next_page = None
    else:
        # if remove this condition test doesn't pass so logic is correct and required by assignment
        raise HTTPException(status_code=404, detail="No movies found.")
    result = await db.execute(select(MovieModel).order_by(MovieModel.id).limit(per_page).offset(start))
    movies_db = result.scalars().all()
    movies = [MovieDetailResponseSchema.model_validate(movie, from_attributes=True) for movie in list(movies_db)]
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


def build_url(request: Request, page: int, per_page: int = 10):
    url = str(request.url.replace_query_params(page=page, per_page=per_page))
    return url
