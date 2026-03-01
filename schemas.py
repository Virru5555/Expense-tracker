from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime

class UserCreate(BaseModel):
    username: str
    password: str

class ExpenseCreate(BaseModel):
    title: str
    category: str
    amount: float
    created_at: Optional[datetime] = None
    
class ExpenseOut(BaseModel):
    id: int
    title: str
    category: str
    amount: float
    created_at: datetime

    class Config:
        orm_mode = True