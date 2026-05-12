-- ============================================================
-- SETUP DATABASE PERPUSPBJT
-- Jalankan di phpMyAdmin > tab SQL
-- ============================================================

USE perpuspbjt;

-- ── TABEL USERS ──
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','petugas') DEFAULT 'petugas',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── TABEL BOOKS ──
CREATE TABLE IF NOT EXISTS books (
    id VARCHAR(20) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150) NOT NULL,
    category VARCHAR(100) DEFAULT 'Umum',
    status ENUM('tersedia','dipinjam','terlambat') DEFAULT 'tersedia',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── TABEL LOANS ──
CREATE TABLE IF NOT EXISTS loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id VARCHAR(20) NOT NULL,
    user_id INT NOT NULL,
    borrower_name VARCHAR(150) NOT NULL,
    member_id VARCHAR(50) NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    status ENUM('dipinjam','terlambat','dikembalikan') DEFAULT 'dipinjam',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ── DATA AWAL ──

-- User default (password: 123)
INSERT IGNORE INTO users (username, password, role) VALUES
('admin', '123', 'admin'),
('petugas', '456', 'petugas');

-- Contoh buku
INSERT IGNORE INTO books (id, title, author, category, status) VALUES
('BOOK-001', 'Bumi Manusia', 'Pramoedya Ananta Toer', 'Fiksi', 'dipinjam'),
('BOOK-002', 'Laskar Pelangi', 'Andrea Hirata', 'Fiksi', 'tersedia'),
('BOOK-003', 'Sapiens', 'Yuval Noah Harari', 'Non-Fiksi', 'dipinjam'),
('BOOK-004', 'Clean Code', 'Robert C. Martin', 'Teknik', 'tersedia'),
('BOOK-005', 'Atomic Habits', 'James Clear', 'Non-Fiksi', 'tersedia'),
('BOOK-006', 'Dune', 'Frank Herbert', 'Fiksi', 'tersedia'),
('BOOK-007', 'Sejarah Indonesia Modern', 'M.C. Ricklefs', 'Sejarah', 'tersedia'),
('BOOK-008', 'Ikigai', 'Hector Garcia', 'Non-Fiksi', 'tersedia');

-- Contoh peminjaman
INSERT IGNORE INTO loans (book_id, user_id, borrower_name, member_id, borrow_date, due_date, status) VALUES
('BOOK-001', 1, 'Andi Saputra', 'MBR-001', '2025-04-01', '2025-04-15', 'dipinjam'),
('BOOK-003', 1, 'Budi Prasetyo', 'MBR-002', '2025-04-05', '2025-04-30', 'dipinjam');