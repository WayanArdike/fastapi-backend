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
# APP (IMPORTANT FOR VERCEL)
# =========================
app = FastAPI()

# =========================
# CORS
# =========================
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
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

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

class RequestRekomendasi(BaseModel):
    genre: str
    subgenre: str

# =========================
# STATIC
# =========================
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "static/images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# =========================
# DATASET
# =========================
DATASET_PATH = BASE_DIR / "dataset_buku.csv"

if DATASET_PATH.exists():
    df = pd.read_csv(DATASET_PATH)
else:
    df = pd.DataFrame(columns=[
        "judul","pengarang","klasifikasi","content","image_url"
    ])

df = df.fillna("")

vectorizer = TfidfVectorizer()
tfidf_matrix = None
search_log = Counter()

def update_tfidf():
    global tfidf_matrix
    if len(df) == 0:
        tfidf_matrix = None
        return
    tfidf_matrix = vectorizer.fit_transform(df["content"])

update_tfidf()

# =========================
# ROOT (IMPORTANT FOR VERCEL TEST)
# =========================
@app.get("/")
def root():
    return {"status": "API running"}

# =========================
# LOGIN
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
def get_books():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM books ORDER BY title")
    data = cur.fetchall()

    db.close()
    return data

@app.get("/books/available")
def available_books():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM books
        WHERE borrowed_count < stock
        ORDER BY title
    """)

    data = cur.fetchall()
    db.close()
    return data

@app.get("/books/search")
def search_books(q: str = ""):
    db = get_db()
    cur = db.cursor()

    like = f"%{q}%"

    cur.execute("""
        SELECT * FROM books
        WHERE title ILIKE %s
        OR author ILIKE %s
        OR id ILIKE %s
    """, (like, like, like))

    data = cur.fetchall()
    db.close()
    return data

# =========================
# BORROW
# =========================
@app.post("/loans/borrow")
def borrow(data: BorrowModel):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM members WHERE nim=%s", (data.nim,))
    member = cur.fetchone()

    if not member:
        db.close()
        raise HTTPException(400, "NIM tidak ditemukan")

    cur.execute("SELECT * FROM books WHERE id=%s", (data.book_id,))
    book = cur.fetchone()

    if not book:
        db.close()
        raise HTTPException(404, "Book not found")

    if book["borrowed_count"] >= book["stock"]:
        db.close()
        raise HTTPException(400, "Stock habis")

    today = date.today().isoformat()

    cur.execute("""
        INSERT INTO loans (
            book_id,user_id,borrower_name,
            member_id,phone,borrow_date,due_date,status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.book_id,
        data.user_id,
        data.borrower_name,
        data.nim,
        data.phone,
        today,
        data.due_date,
        "dipinjam"
    ))

    cur.execute("""
        UPDATE books
        SET borrowed_count = borrowed_count + 1
        WHERE id=%s
    """, (data.book_id,))

    db.commit()
    db.close()

    return {"message": "OK borrowed"}

# =========================
# IMPORTANT: VERCEL ENTRYPOINT
# =========================
# TIDAK ADA uvicorn.run()
