from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime

import models
import schemas
from database import engine, SessionLocal
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

app = FastAPI(title="Personal Expense Tracker API")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB ----------------
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- AUTH DEPENDENCY ----------------
def get_current_user_id(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload["user_id"]

# ---------------- REGISTER ----------------
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    username = user.username.lower().strip()

    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = models.User(
        username=username,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}

# ---------------- LOGIN ----------------
@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    username = user.username.lower().strip()

    db_user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"user_id": db_user.id})

    return {
        "message": "Login successful",
        "token": token,
        "username": db_user.username
    }

# ---------------- ADD EXPENSE ----------------
@app.post("/expenses")
def add_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    exp = models.Expense(
        title=expense.title,
        category=expense.category,
        amount=expense.amount,

        # ✅ USE USER SELECTED DATE
        created_at=expense.created_at,

        user_id=user_id
    )

    db.add(exp)
    db.commit()
    return {"message": "Expense added"}


# ---------------- GET EXPENSES ----------------
@app.get("/expenses")
def get_expenses(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return db.query(models.Expense)\
        .filter(models.Expense.user_id == user_id)\
        .order_by(models.Expense.created_at.desc())\
        .all()

# ---------------- DELETE EXPENSE ----------------
@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    exp = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == user_id
    ).first()

    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(exp)
    db.commit()
    return {"message": "Expense deleted"}

# ---------------- EDIT EXPENSE ----------------
@app.put("/expenses/{expense_id}")
def edit_expense(
    expense_id: int,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    exp = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == user_id
    ).first()

    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    exp.title = expense.title
    exp.category = expense.category
    exp.amount = expense.amount
    if expense.created_at:
        exp.created_at = expense.created_at

    db.commit()
    return {"message": "Expense updated"}

# ---------------- MONTHLY SUMMARY ----------------
@app.get("/expenses/summary/month-detail/{year}/{month}")
def monthly_detail_summary(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        extract("year", models.Expense.created_at) == year,
        extract("month", models.Expense.created_at) == month
    ).order_by(models.Expense.created_at).all()

    summary = {}
    month_total = 0

    for exp in expenses:
        day = exp.created_at.date().isoformat()

        if day not in summary:
            summary[day] = {
                "date": day,
                "expenses": [],
                "day_total": 0
            }

        summary[day]["expenses"].append({
            "time": exp.created_at.strftime("%H:%M"),
            "title": exp.title,
            "category": exp.category,
            "amount": exp.amount
        })

        summary[day]["day_total"] += exp.amount
        month_total += exp.amount

    return {
        "year": year,
        "month": month,
        "days": list(summary.values()),
        "month_total": month_total
    }
