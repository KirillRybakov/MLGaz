from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    # Используем Field для добавления ограничений на поле
    password: str = Field(
        ...,  # Три точки означают, что поле обязательно
        min_length=6,
        max_length=72
    )

class User(UserBase):
    id: int

    class Config:
        from_attributes = True