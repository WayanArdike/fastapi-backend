from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import mysql.connector
import pandas as pd

from datetime import date, datetime
from pathlib import Path
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Sistem Perpustakaan API",
    description="API Sistem Perpustakaan + Rekomendasi Buku",
    version="1.0.0",
)

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
# STATIC FILES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset_buku.csv"
IMAGES_DIR = BASE_DIR / "static/images"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# =========================================================
# DATABASE
# =========================================================

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="perpuspbjt"
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


class BorrowModel(BaseModel):
    user_id: int
    book_id: str
    borrower_name: str
    member_id: str
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
# LOAD DATASET
# =========================================================

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

# =========================================================
# TF-IDF
# =========================================================

vectorizer = TfidfVectorizer(stop_words=None)
tfidf_matrix = None
search_log = Counter()


def update_tfidf():
    global tfidf_matrix

    if len(df) == 0:
        tfidf_matrix = None
        return

    tfidf_matrix = vectorizer.fit_transform(df["content"])


update_tfidf()

# =========================================================
# ROOT
# =========================================================

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>Sistem Perpustakaan API</title>
        </head>
        <body style="font-family: Arial; padding: 40px;">
            <h1>Sistem Perpustakaan API</h1>
            <p>Server berjalan dengan normal.</p>

            <ul>
                <li><a href="/docs">Swagger Docs</a></li>
                <li><a href="/books">Books API</a></li>
                <li><a href="/members">Members API</a></li>
            </ul>
        </body>
    </html>
    """

# =========================================================
# AUTH
# =========================================================

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

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah"
        )

    return {
        "user_id": user["id"],
        "username": user["username"],
        "role": user.get("role", "petugas")
    }

# =========================================================
# BOOKS
# =========================================================

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

    query_text = f"{data.genre} {data.subgenre}".strip()

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
# MEMBERS
# =========================================================

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

# =========================================================
# STATS
# =========================================================

@app.get("/stats")
def get_stats():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT COUNT(*) as total
        FROM books
    """)

    total = cur.fetchone()["total"]

    db.close()

    return {
        "total_books": total
    }

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )