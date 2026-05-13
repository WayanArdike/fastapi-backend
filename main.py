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


# =========================================================
# APP
# =========================================================

app = FastAPI(title="Sistem Perpustakaan API")


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = "postgresql://postgres.xshxmatydgamddlrrzgs:5rRCHdMbqWL88ZLh@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"


def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


# =========================================================
# MODELS
# =========================================================

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


# =========================================================
# DATASET REKOMENDASI
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "dataset_buku.csv"

IMAGES_DIR = BASE_DIR / "static/images"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/images",
    StaticFiles(directory=IMAGES_DIR),
    name="images"
)

if DATASET_PATH.exists():

    df = pd.read_csv(DATASET_PATH)

else:

    df = pd.DataFrame(columns=[
        "judul",
        "pengarang",
        "klasifikasi",
        "status",
        "genre_utama",
        "subgenre",
        "genre",
        "content",
        "image_url"
    ])

df = df.fillna("")


def normalize_filename(text):
    return text.lower().strip().replace(" ", "_")


def find_existing_image(judul):

    base_name = normalize_filename(judul)

    for ext in ["jpg", "jpeg", "png", "webp"]:

        file_path = IMAGES_DIR / f"{base_name}.{ext}"

        if file_path.exists():
            return f"/images/{base_name}.{ext}"

    return "/images/no_cover.png"


if len(df) > 0:
    df["image_url"] = df["judul"].apply(find_existing_image)

vectorizer = TfidfVectorizer(stop_words=None)

tfidf_matrix = None


def update_tfidf():

    global tfidf_matrix

    if len(df) == 0:

        tfidf_matrix = None
        return

    tfidf_matrix = vectorizer.fit_transform(df["content"])


update_tfidf()

search_log = Counter()


# =========================================================
# AUTH
# =========================================================

@app.post("/api/login")
def login(data: LoginModel):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE username=%s
        AND password=%s
    """, (
        data.username,
        data.password
    ))

    user = cur.fetchone()

    db.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Username atau password salah"
        )

    return {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }


# =========================================================
# BOOKS
# =========================================================

@app.get("/books")
def get_books():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM books
        ORDER BY title
    """)

    books = cur.fetchall()

    db.close()

    return books


@app.get("/books/available")
def get_available_books():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM books
        WHERE borrowed_count < stock
        ORDER BY title
    """)

    books = cur.fetchall()

    db.close()

    return books


@app.get("/books/search")
def search_books(q: str = ""):

    db = get_db()
    cur = db.cursor()

    search = f"%{q}%"

    cur.execute("""
        SELECT *
        FROM books
        WHERE
            title ILIKE %s
            OR author ILIKE %s
            OR id ILIKE %s
        ORDER BY title
    """, (
        search,
        search,
        search
    ))

    books = cur.fetchall()

    db.close()

    return books


@app.post("/books")
def add_book(book: BookModel):

    db = get_db()
    cur = db.cursor()

    try:

        cur.execute("""
            INSERT INTO books (
                id,
                title,
                author,
                category,
                stock,
                borrowed_count
            )
            VALUES (
                %s,%s,%s,%s,%s,0
            )
        """, (
            book.id,
            book.title,
            book.author,
            book.category,
            book.stock
        ))

        db.commit()

    except psycopg2.IntegrityError:

        db.rollback()
        db.close()

        raise HTTPException(
            status_code=400,
            detail="ID buku sudah ada"
        )

    db.close()

    return {
        "message": "Buku berhasil ditambahkan"
    }


@app.delete("/books/{book_id}")
def delete_book(book_id: str):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM books
        WHERE id=%s
    """, (book_id,))

    book = cur.fetchone()

    if not book:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Buku tidak ditemukan"
        )

    if book["borrowed_count"] > 0:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="Buku masih dipinjam"
        )

    cur.execute("""
        DELETE FROM books
        WHERE id=%s
    """, (book_id,))

    db.commit()

    db.close()

    return {
        "message": "Buku berhasil dihapus"
    }


# =========================================================
# LOANS
# =========================================================

@app.get("/loans")
def get_loans():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT
            l.*,
            b.title AS book_title,
            b.author AS book_author
        FROM loans l
        JOIN books b
        ON l.book_id = b.id
        ORDER BY l.borrow_date DESC
    """)

    loans = cur.fetchall()

    db.close()

    for loan in loans:

        for k, v in loan.items():

            if isinstance(v, (date, datetime)):
                loan[k] = str(v)

    return loans


@app.post("/loans/borrow")
def borrow_book(data: BorrowModel):

    db = get_db()
    cur = db.cursor()

    # cek member pakai NIM
    cur.execute("""
        SELECT *
        FROM members
        WHERE nim=%s
    """, (data.nim,))

    member = cur.fetchone()

    if not member:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="NIM tidak terdaftar"
        )

    # cek buku
    cur.execute("""
        SELECT *
        FROM books
        WHERE id=%s
    """, (data.book_id,))

    book = cur.fetchone()

    if not book:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Buku tidak ditemukan"
        )

    if book["borrowed_count"] >= book["stock"]:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Stok habis"
        )

    today = date.today().isoformat()

    cur.execute("""
        INSERT INTO loans (
            book_id,
            user_id,
            borrower_name,
            member_id,
            phone,
            borrow_date,
            due_date,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
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

    return {
        "message": f"{book['title']} berhasil dipinjam"
    }


@app.post("/loans/return")
def return_book(data: ReturnModel):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM loans
        WHERE
            book_id=%s
            AND status IN ('dipinjam','terlambat')
        ORDER BY borrow_date DESC
        LIMIT 1
    """, (data.book_id,))

    loan = cur.fetchone()

    if not loan:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Peminjaman aktif tidak ditemukan"
        )

    today = date.today().isoformat()

    # =========================
    # UPDATE LOAN
    # =========================

    cur.execute("""
        UPDATE loans
        SET
            status='dikembalikan',
            return_date=%s
        WHERE id=%s
    """, (
        today,
        loan["id"]
    ))

    # =========================
    # UPDATE BOOK
    # =========================

    cur.execute("""
        UPDATE books
        SET borrowed_count =
            GREATEST(borrowed_count - 1, 0)
        WHERE id=%s
    """, (data.book_id,))

    db.commit()

    db.close()

    return {
        "message": "Buku berhasil dikembalikan"
    }


# =========================================================
# STATS
# =========================================================

@app.get("/stats")
def get_stats():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM books
    """)

    total = cur.fetchone()["total"]

    cur.execute("""
        SELECT COALESCE(SUM(borrowed_count), 0) AS total
        FROM books
    """)

    borrowed = cur.fetchone()["total"]

    cur.execute("""
        SELECT
            COUNT(*) AS total
        FROM books
        WHERE borrowed_count < stock
    """)

    available = cur.fetchone()["total"]

    cur.execute("""
        UPDATE loans
        SET status='terlambat'
        WHERE
            due_date < CURRENT_DATE
            AND status='dipinjam'
    """)

    db.commit()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM loans
        WHERE status='terlambat'
    """)

    overdue = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM members
    """)

    members = cur.fetchone()["total"]

    db.close()

    return {
        "total": total,
        "borrowed": borrowed,
        "available": available,
        "overdue": overdue,
        "members": members
    }


# =========================================================
# MEMBERS
# =========================================================

@app.get("/members")
def get_members():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM members
        ORDER BY id DESC
    """)

    members = cur.fetchall()

    db.close()

    return members


@app.get("/members/search")
def search_members(q: str = ""):

    db = get_db()
    cur = db.cursor()

    search = f"%{q}%"

    cur.execute("""
        SELECT *
        FROM members
        WHERE
            name ILIKE %s
            OR nim ILIKE %s
            OR member_code ILIKE %s
        ORDER BY id DESC
    """, (
        search,
        search,
        search
    ))

    results = cur.fetchall()

    db.close()

    return results


@app.post("/members")
def add_member(data: MemberModel):

    db = get_db()
    cur = db.cursor()

    try:

        cur.execute("""
            INSERT INTO members (
                member_code,
                name,
                nim,
                major,
                phone,
                address
            )
            VALUES (
                %s,%s,%s,%s,%s,%s
            )
        """, (
            data.member_code,
            data.name,
            data.nim,
            data.major,
            data.phone,
            data.address
        ))

        db.commit()

    except psycopg2.IntegrityError:

        db.rollback()

        db.close()

        raise HTTPException(
            status_code=400,
            detail="Kode member sudah ada"
        )

    db.close()

    return {
        "message": "Member berhasil ditambahkan"
    }


# =========================================================
# RECOMMENDATION
# =========================================================

@app.post("/recommend")
def recommend(data: RequestRekomendasi):

    if tfidf_matrix is None:

        return {
            "recommendations": [],
            "popular": []
        }

    query_text = f"{data.genre} {data.subgenre}"

    query_vec = vectorizer.transform([query_text])

    similarity = cosine_similarity(
        query_vec,
        tfidf_matrix
    )[0]

    top_idx = similarity.argsort()[-5:][::-1]

    hasil = []

    for i in top_idx:

        row = df.iloc[i]

        hasil.append({
            "judul": row["judul"],
            "pengarang": row["pengarang"],
            "klasifikasi": row["klasifikasi"],
            "image_url": row["image_url"],
            "description": f"Buku karya {row['pengarang']}"
        })

        search_log[row["judul"]] += 1

    return {
        "recommendations": hasil,
        "popular": [
            j for j, _ in search_log.most_common(5)
        ]
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "API Perpustakaan aktif"
    }


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
