from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from datetime import date, datetime
import httpx
from fastapi import Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import shutil
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import uuid
import os
import pandas as pd
import shutil

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.metrics.pairwise import cosine_similarity

from collections import Counter

import uuid

from fastapi import (
    UploadFile,
    File,
    Form,
    Query
)

from fastapi.responses import HTMLResponse

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Sistem Perpustakaan API")

# ══════════════════════════════════════════════
# CORS
# ══════════════════════════════════════════════

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="perpuspbjt"
    )

# ══════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════

class LoginModel(BaseModel):
    username: str
    password: str


class BookModel(BaseModel):
    id: str
    title: str
    author: str
    category: str


class BorrowModel(BaseModel):
    user_id: int
    book_id: str
    borrower_name: str
    member_id: str
    phone: str
    due_date: str


class ReturnModel(BaseModel):
    book_id: str


class ScanModel(BaseModel):
    image_base64: str

class MemberModel(BaseModel):
    member_code:str
    name: str
    nim:str
    major:str
    phone:str
    address:str

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset_buku.csv"
IMAGES_DIR = BASE_DIR / "static/images"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# INIT APP
# =====================
app = FastAPI(title="Sistem Rekomendasi Buku")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# =====================
# LOAD DATASET
# =====================
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

df["image_url"] = df["judul"].apply(find_existing_image)

# =====================
# TF-IDF SETUP
# =====================
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

# ══════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════

@app.post("/login")
def login(data: LoginModel):

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (data.username, data.password)
    )

    user = cur.fetchone()

    db.close()

    if user:
        return {
            "user_id": user["id"],
            "username": user["username"],
            "role": user.get("role", "petugas")
        }

    raise HTTPException(
        status_code=401,
        detail="Username atau password salah"
    )


# ══════════════════════════════════════════════
# BOOKS
# ══════════════════════════════════════════════

@app.get("/books")
def get_books():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM books
        ORDER BY id
    """)

    books = cur.fetchall()

    db.close()

    return books


@app.get("/books/available")
def get_available_books():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM books
        WHERE status='tersedia'
        ORDER BY title
    """)

    books = cur.fetchall()

    db.close()

    return books


@app.get("/books/search")
def search_books(q: str = ""):

    db = get_db()
    cur = db.cursor(dictionary=True)

    like = f"%{q}%"

    cur.execute("""
        SELECT *
        FROM books
        WHERE title LIKE %s
        OR author LIKE %s
        OR id LIKE %s
    """, (like, like, like))

    books = cur.fetchall()

    db.close()

    return books

class RequestRekomendasi(BaseModel):
    genre: str
    subgenre: str

@app.post("/recommend")
def recommend(data: RequestRekomendasi):

    if tfidf_matrix is None:
        return {"recommendations": [], "popular": []}

    query_text = f"{data.genre} {data.subgenre}".strip()
    query_vec = vectorizer.transform([query_text])

    similarity = cosine_similarity(query_vec, tfidf_matrix)[0]
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
        "popular": [j for j, _ in search_log.most_common(5)]
    }



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
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                'tersedia'
            )
        """, (
            book.id,
            book.title,
            book.author,
            book.category
        ))

        db.commit()

    except mysql.connector.IntegrityError:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="ID buku sudah ada"
        )

    db.close()

    return {
        "message":
        f"Buku '{book.title}' berhasil ditambahkan"
    }


@app.delete("/books/{book_id}")
def delete_book(book_id: str):

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT status FROM books WHERE id=%s",
        (book_id,)
    )

    book = cur.fetchone()

    if not book:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Buku tidak ditemukan"
        )

    if book["status"] == "dipinjam":
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Tidak bisa hapus buku yang sedang dipinjam"
        )

    cur.execute(
        "DELETE FROM books WHERE id=%s",
        (book_id,)
    )

    db.commit()

    db.close()

    return {
        "message": "Buku berhasil dihapus"
    }


# ══════════════════════════════════════════════
# LOANS
# ══════════════════════════════════════════════

@app.get("/loans")
def get_loans():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            l.*,
            b.title as book_title,
            b.author as book_author
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


@app.get("/loans/active")
def get_active_loans():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            l.*,
            b.title as book_title,
            b.author as book_author
        FROM loans l
        JOIN books b
        ON l.book_id = b.id
        WHERE l.status IN ('dipinjam','terlambat')
        ORDER BY l.due_date ASC
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
    cur = db.cursor(dictionary=True)

    # cek anggota
    print(data.member_id)
    cur.execute("""
            SELECT *
            FROM members
            WHERE member_code=%s
        """, (data.member_id,))

    member = cur.fetchone()

    if not member:

            db.close()

            raise HTTPException(
        status_code=400,
        detail=
        "Mahasiswa belum terdaftar sebagai anggota perpustakaan"
    )

    # cek buku
    cur.execute(
        "SELECT * FROM books WHERE id=%s",
        (data.book_id,)
    )

    book = cur.fetchone()

    if not book:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Buku tidak ditemukan"
        )

    if book["status"] != "tersedia":
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Buku sedang tidak tersedia"
        )

    today = date.today().isoformat()

    # insert peminjaman
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
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        data.book_id,
        data.user_id,
        data.borrower_name,
        data.member_id,
        data.phone,
        today,
        data.due_date,
        "dipinjam"
    ))

    # update status buku
    cur.execute("""
        UPDATE books
        SET status='dipinjam'
        WHERE id=%s
    """, (data.book_id,))

    db.commit()

    db.close()

    return {
        "message":
        f"Buku '{book['title']}' berhasil dipinjam oleh {data.borrower_name}"
    }


@app.post("/loans/return")
def return_book(data: ReturnModel):

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            l.*,
            b.title as book_title
        FROM loans l
        JOIN books b
        ON l.book_id = b.id
        WHERE l.book_id=%s
        AND l.status IN ('dipinjam','terlambat')
        ORDER BY l.borrow_date DESC
        LIMIT 1
    """, (data.book_id,))

    loan = cur.fetchone()

    if not loan:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Tidak ada peminjaman aktif"
        )

    today = date.today().isoformat()

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

    # update status buku
    cur.execute("""
        UPDATE books
        SET status='tersedia'
        WHERE id=%s
    """, (data.book_id,))

    db.commit()

    db.close()

    for k, v in loan.items():
        if isinstance(v, (date, datetime)):
            loan[k] = str(v)

    return {
        "message":
        f"Pengembalian '{loan['book_title']}' berhasil",
        "loan": loan
    }


@app.get("/stats")
def get_stats():

    db = get_db()
    cur = db.cursor(dictionary=True)

    # total buku
    cur.execute("""
        SELECT COUNT(*) as total
        FROM books
    """)

    total = cur.fetchone()["total"]

    # dipinjam
    cur.execute("""
        SELECT COUNT(*) as c
        FROM books
        WHERE status='dipinjam'
    """)

    borrowed = cur.fetchone()["c"]

    # tersedia
    cur.execute("""
        SELECT COUNT(*) as c
        FROM books
        WHERE status='tersedia'
    """)

    available = cur.fetchone()["c"]

    # update terlambat
    cur.execute("""
        UPDATE loans
        SET status='terlambat'
        WHERE due_date < CURDATE()
        AND status='dipinjam'
    """)

    db.commit()

    # total terlambat
    cur.execute("""
        SELECT COUNT(*) as c
        FROM loans
        WHERE status='terlambat'
    """)

    overdue = cur.fetchone()["c"]

    # total anggota
    cur.execute("""
        SELECT COUNT(*) as c
        FROM members
    """)

    members = cur.fetchone()["c"]

    db.close()

    return {
        "total": total,
        "borrowed": borrowed,
        "available": available,
        "overdue": overdue,
        "members": members
    }

# ══════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════

@app.get("/users")
def get_users():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            id,
            username,
            role
        FROM users
    """)

    users = cur.fetchall()

    db.close()

    return users

# ══════════════════════════════════════════════
# MEMBERS
# ══════════════════════════════════════════════

@app.get("/members")
def get_members():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM members
        ORDER BY id DESC
    """)

    members = cur.fetchall()

    db.close()

    return members


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
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
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

    except mysql.connector.IntegrityError:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="Kode anggota sudah ada"
        )

    db.close()

    return {
        "message":
        f"Anggota '{data.name}' berhasil ditambahkan"
    }

@app.put("/members/{member_id}")
def update_member(member_id: int, data: MemberModel):

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("""
            UPDATE members
            SET
                member_code=%s,
                name=%s,
                nim=%s,
                major=%s,
                phone=%s,
                address=%s
            WHERE id=%s
        """, (
            data.member_code,
            data.name,
            data.nim,
            data.major,
            data.phone,
            data.address,
            member_id,
        ))

        if cur.rowcount == 0:
            db.close()
            raise HTTPException(
                status_code=404,
                detail="Anggota tidak ditemukan"
            )

        db.commit()

    except mysql.connector.IntegrityError:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="Kode anggota sudah ada"
        )

    db.close()

    return {
        "message":
        f"Anggota '{data.name}' berhasil diperbarui"
    }

@app.delete("/members/{member_id}")
def delete_member(member_id: int):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        DELETE FROM members
        WHERE id=%s
    """, (member_id,))

    if cur.rowcount == 0:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Anggota tidak ditemukan"
        )

    db.commit()
    db.close()

    return {
        "message": "Anggota berhasil dihapus"
    }

@app.get("/members/search")
def search_members(q: str = ""):

    db = get_db()

    cur = db.cursor(
        dictionary=True
    )

    like = f"%{q}%"

    cur.execute("""
        SELECT *
        FROM members
        WHERE
            name LIKE %s
            OR nim LIKE %s
            OR member_code LIKE %s
    """, (
        like,
        like,
        like
    ))

    data = cur.fetchall()

    db.close()

    return data
# ══════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )