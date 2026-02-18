from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import engine, Base, get_db
from app.models.entry import Entry
from app.schemas.entry import EntryCreate, EntryOut
from app.services.metrics import (
    compute_summary,
    compute_trends,
    compute_correlations,
    generate_recommendations,
)

app = FastAPI(title="Time Perception Analyzer", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/entries", response_model=EntryOut)
async def create_entry(payload: EntryCreate, db: AsyncSession = Depends(get_db)):
    entry = Entry(**payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@app.get("/api/entries", response_model=list[EntryOut])
async def list_entries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry).order_by(Entry.created_at.desc()))
    return result.scalars().all()


@app.get("/api/insights/summary")
async def insights_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry))
    entries = result.scalars().all()
    return compute_summary(entries)


@app.get("/api/insights/trends")
async def insights_trends(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry))
    entries = result.scalars().all()
    return compute_trends(entries)


@app.get("/api/insights/correlations")
async def insights_correlations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry))
    entries = result.scalars().all()
    return compute_correlations(entries)


@app.get("/api/insights/scatter")
async def insights_scatter(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry))
    entries = result.scalars().all()

    data = []
    for e in entries:
        est = max(e.estimated_min, 1)
        percent_error = ((e.actual_min - est) / est) * 100
        data.append({"difficulty": e.difficulty, "percent_error": round(percent_error, 2)})

    return data


@app.get("/api/insights/recommendations")
async def insights_recommendations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry))
    entries = result.scalars().all()
    return generate_recommendations(entries)
