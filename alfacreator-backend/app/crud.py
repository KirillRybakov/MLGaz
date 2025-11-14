# alfacreator-backend/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models
from typing import Optional
from app.schemas import user as user_schema
from app.core.security import get_password_hash


async def create_history_entry(db: AsyncSession, request_type: str, input_data: dict, output_data: dict):
    db_entry = models.History(request_type=request_type, input_data=input_data, output_data=output_data)
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry


async def get_history_entries(db: AsyncSession, request_type: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = select(models.History)
    if request_type:
        query = query.where(models.History.request_type == request_type)

    query = query.order_by(models.History.id.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_user_by_email(db: AsyncSession, email: str):
    # Используем асинхронный подход с select и execute
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: user_schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user