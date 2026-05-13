from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from datetime import date, datetime
from pathlib import Path
from collections import Counter

import psycopg2
from psycopg2.extras import RealDictCursor

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# APP
# =========================
app = FastAPI(title="Sistem Perpustakaan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB
# =========================
DATABASE_URL = "postgresql://postgres.xshxmatydgamddlrrzgs:5rRCHdMbqWL88ZLh@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# =========================
# MODELS
# =========================
class LoginModel(BaseModel):
    username: str
    password: str

class BookModel(BaseModel):
    id: str
    title: str
    author: str
    category: str
    stock: int

class BorrowModel(BaseModel):
    user_id: int
    book_id: str
    borrower_name: str
    nim: str
    phone: str
    due_date: str

class ReturnModel(BaseModel):
    book_id: str

class MemberModel(BaseModel):
    member_code: str
    name: str
    nim: str
    major: str
    phone: str
    address: str

# =========================
# DATASET
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset_buku.csv"

df = pd.read_csv(DATASET_PATH) if DATASET_PATH.exists() else pd.DataFrame()
df = df.fillna("")

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(df["content"]) if len(df) else None
search_log = Counter()

# =========================
# AUTH
# =========================
@app.post("/api/login")
def login(data: LoginModel):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM users
        WHERE username=%s AND password=%s
    """, (data.username, data.password))

    user = cur.fetchone()
    db.close()

    if not user:
        raise HTTPException(401, "Login gagal")

    return user

# =========================
# BOOKS
# =========================
@app.get("/books")
def books():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM books ORDER BY title")
    data = cur.fetchall()
    db.close()
    return data

@app.get("/books/available")
def available():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM books WHERE borrowed_count < stock")
    data = cur.fetchall()
    db.close()
    return data

# =========================
# BORROW (FIXED: NIM ONLY)
# =========================
@app.post("/loans/borrow")
def borrow(data: BorrowModel):
    db = get_db()
    cur = db.cursor()

    # CHECK MEMBER BY NIM
    cur.execute("SELECT * FROM members WHERE nim=%s", (data.nim,))
    member = cur.fetchone()

    if not member:
        db.close()
        raise HTTPException(400, "NIM tidak terdaftar")

    # CHECK BOOK
    cur.execute("SELECT * FROM books WHERE id=%s", (data.book_id,))
    book = cur.fetchone()

    if not book:
        db.close()
        raise HTTPException(404, "Buku tidak ditemukan")

    if book["borrowed_count"] >= book["stock"]:
        db.close()
        raise HTTPException(400, "Stok habis")

    today = date.today().isoformat()

    cur.execute("""
        INSERT INTO loans (
            book_id, user_id, borrower_name,
            nim, phone, borrow_date, due_date, status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,'dipinjam')
    """, (
        data.book_id,
        data.user_id,
        data.borrower_name,
        data.nim,
        data.phone,
        today,
        data.due_date
    ))

    cur.execute("""
        UPDATE books
        SET borrowed_count = borrowed_count + 1
        WHERE id=%s
    """, (data.book_id,))

    db.commit()
    db.close()

    return {"message": "Buku berhasil dipinjam"}

# =========================
# RETURN
# =========================
@app.post("/loans/return")
def return_book(data: ReturnModel):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM loans
        WHERE book_id=%s AND status IN ('dipinjam','terlambat')
        ORDER BY borrow_date DESC LIMIT 1
    """, (data.book_id,))

    loan = cur.fetchone()

    if not loan:
        db.close()
        raise HTTPException(404, "Loan tidak ditemukan")

    today = date.today().isoformat()

    cur.execute("""
        UPDATE loans
        SET status='dikembalikan', return_date=%s
        WHERE id=%s
    """, (today, loan["id"]))

    cur.execute("""
        UPDATE books
        SET borrowed_count = GREATEST(borrowed_count - 1, 0)
        WHERE id=%s
    """, (data.book_id,))

    db.commit()
    db.close()

    return {"message": "Buku dikembalikan"}

# =========================
# STATS
# =========================
@app.get("/stats")
def stats():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM books")
    total = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM members")
    members = cur.fetchone()["count"]

    db.close()

    return {
        "total_books": total,
        "members": members
    }

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "API aktif"}

# =========================
# IMPORTANT FOR VERCEL
# =========================
handler = app
