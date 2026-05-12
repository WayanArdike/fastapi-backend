-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: May 12, 2026 at 01:28 PM
-- Server version: 8.4.3
-- PHP Version: 8.3.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `perpuspbjt`
--

-- --------------------------------------------------------

--
-- Table structure for table `books`
--

CREATE TABLE `books` (
  `id` varchar(20) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(150) NOT NULL,
  `category` varchar(100) DEFAULT 'Umum',
  `status` enum('tersedia','dipinjam','terlambat') DEFAULT 'tersedia',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `books`
--

INSERT INTO `books` (`id`, `title`, `author`, `category`, `status`, `created_at`) VALUES
('-', 'KAMUS LENGKAP 900 MILYAR', 'lingkar media', 'Fiksi', 'tersedia', '2026-05-07 04:34:41'),
('8990092030141', 'DINO', 'anin', 'Fiksi', 'tersedia', '2026-05-07 04:07:49'),
('9786239608071', 'Ketua BEM and His Secret Wife', 'La Shaleta', 'Fiksi', 'dipinjam', '2026-05-12 12:28:04'),
('9789790331242', 'HIDUP MAKIN SUSAH, KALAU BANYAK YANG HOBINYA BOHONG!', 'Saiful Hadi El-Sutha', 'Lainnya', 'dipinjam', '2026-05-12 12:31:32'),
('BOOK-001', 'Bumi Manusia', 'Pramoedya Ananta Toer', 'Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-002', 'Laskar Pelangi', 'Andrea Hirata', 'Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-003', 'Sapiens', 'Yuval Noah Harari', 'Non-Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-004', 'Clean Code', 'Robert C. Martin', 'Teknik', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-005', 'Atomic Habits', 'James Clear', 'Non-Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-006', 'Dune', 'Frank Herbert', 'Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-007', 'Sejarah Indonesia Modern', 'M.C. Ricklefs', 'Sejarah', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-008', 'Ikigai', 'Hector Garcia', 'Non-Fiksi', 'tersedia', '2026-04-30 11:16:03'),
('BOOK-009', 'ayok putus', 'anandaryu', 'Fiksi', 'tersedia', '2026-04-30 11:16:50'),
('BOOK-010', 'CAMPUS', 'CAMPUS', 'Teknik', 'tersedia', '2026-04-30 11:32:55');

-- --------------------------------------------------------

--
-- Table structure for table `loans`
--

CREATE TABLE `loans` (
  `id` int NOT NULL,
  `book_id` varchar(20) NOT NULL,
  `user_id` int NOT NULL,
  `borrower_name` varchar(150) NOT NULL,
  `member_id` varchar(50) NOT NULL,
  `borrow_date` date NOT NULL,
  `due_date` date NOT NULL,
  `return_date` date DEFAULT NULL,
  `status` enum('dipinjam','terlambat','dikembalikan') DEFAULT 'dipinjam',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `phone` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `loans`
--

INSERT INTO `loans` (`id`, `book_id`, `user_id`, `borrower_name`, `member_id`, `borrow_date`, `due_date`, `return_date`, `status`, `created_at`, `phone`) VALUES
(1, 'BOOK-001', 1, 'Andi Saputra', 'MBR-001', '2025-04-01', '2025-04-15', '2026-04-30', 'dikembalikan', '2026-04-30 11:16:03', NULL),
(2, 'BOOK-003', 1, 'Budi Prasetyo', 'MBR-002', '2025-04-05', '2025-04-30', '2026-04-30', 'dikembalikan', '2026-04-30 11:16:03', NULL),
(3, 'BOOK-009', 1, 'Salwa', '-', '2026-04-30', '2026-05-14', '2026-05-03', 'dikembalikan', '2026-04-30 11:17:14', NULL),
(4, 'BOOK-010', 1, 'ajeng', '-', '2026-04-30', '2026-05-14', '2026-04-30', 'dikembalikan', '2026-04-30 11:33:16', NULL),
(5, 'BOOK-001', 1, 'aan', '23.1.9.0024', '2026-04-30', '2026-05-14', '2026-05-03', 'dikembalikan', '2026-04-30 11:51:33', NULL),
(6, 'BOOK-009', 1, 'aul', '-', '2026-05-03', '2026-05-17', '2026-05-03', 'dikembalikan', '2026-05-03 13:22:42', NULL),
(7, 'BOOK-002', 1, 'iin', '-', '2026-05-03', '2026-05-17', '2026-05-06', 'dikembalikan', '2026-05-03 13:53:03', NULL),
(8, 'BOOK-010', 1, 'uun', '-', '2026-05-03', '2026-05-17', '2026-05-03', 'dikembalikan', '2026-05-03 14:20:55', NULL),
(9, '8990092030141', 1, 'anin', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:09:09', NULL),
(10, 'BOOK-010', 1, 'aan', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:13:23', NULL),
(11, 'BOOK-010', 1, 'ii', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:14:55', NULL),
(12, '8990092030141', 1, 'ui', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:22:12', NULL),
(13, '8990092030141', 1, 'ika', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:29:55', NULL),
(14, '-', 1, 'ika', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:35:05', NULL),
(15, '8990092030141', 1, 'kia', '-', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 04:42:12', NULL),
(16, 'BOOK-009', 1, 'uun', '99', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:15:41', NULL),
(17, 'BOOK-001', 1, 'aulan', '87', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:25:47', NULL),
(18, 'BOOK-001', 1, 'ratih', '90', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:36:52', NULL),
(19, 'BOOK-010', 1, 'bbbb', '768', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:41:06', NULL),
(20, 'BOOK-005', 1, 'tuti', '89', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:44:03', NULL),
(21, 'BOOK-010', 1, 'uun', '90', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 12:53:39', NULL),
(22, 'BOOK-009', 1, 'yuyi', '78', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 13:01:28', '0812345678'),
(23, 'BOOK-010', 1, 'yoi', '56', '2026-05-07', '2026-05-21', '2026-05-07', 'dikembalikan', '2026-05-07 13:04:57', '083188582739'),
(24, 'BOOK-009', 1, 'iup', '930', '2026-05-08', '2026-05-21', '2026-05-08', 'dikembalikan', '2026-05-07 23:54:59', '09198891'),
(25, '8990092030141', 1, 'salwa', '-', '2026-05-08', '2026-05-22', '2026-05-08', 'dikembalikan', '2026-05-08 00:21:55', '192891072'),
(26, '-', 1, 'iin', '-', '2026-05-08', '2026-05-22', '2026-05-08', 'dikembalikan', '2026-05-08 01:08:23', '089210018'),
(27, 'BOOK-002', 1, 'jkajoai', '-', '2026-05-08', '2026-05-22', '2026-05-08', 'dikembalikan', '2026-05-08 01:15:18', '0902802'),
(28, 'BOOK-009', 1, 'Diajeng Salwa Aulan Ni\'mah', '23.1.9.0024', '2026-05-08', '2026-05-22', '2026-05-08', 'dikembalikan', '2026-05-08 01:29:01', '085641578755'),
(30, 'BOOK-010', 1, 'Diajeng Salwa Aulan Ni\'mah', '23.1.9.0024', '2026-05-11', '2026-05-25', '2026-05-11', 'dikembalikan', '2026-05-11 10:59:29', '085641578755'),
(31, '9786239608071', 1, 'Diajeng Salwa Aulan Ni\'mah', '23.1.9.0024', '2026-05-12', '2026-05-26', NULL, 'dipinjam', '2026-05-12 12:28:30', '085641578755'),
(32, '9789790331242', 1, 'Heni Melita Ulfianah', '23.1.9.0016', '2026-05-12', '2026-05-26', NULL, 'dipinjam', '2026-05-12 12:31:46', '083837331211');

-- --------------------------------------------------------

--
-- Table structure for table `members`
--

CREATE TABLE `members` (
  `id` int NOT NULL,
  `member_code` varchar(30) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `nim` varchar(30) NOT NULL,
  `major` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `members`
--

INSERT INTO `members` (`id`, `member_code`, `name`, `nim`, `major`, `phone`, `address`, `created_at`) VALUES
(4, '23.1.9.0024', 'Diajeng Salwa Aulan Ni\'mah', '23.1.9.0024', 'Teknik Informatika', '085641578755', 'Brebes Larangan', '2026-05-08 01:28:33'),
(5, '23.1.9.0016', 'Heni Melita Ulfianah', '23.1.9.0016', 'Teknik Informatika', '083837331211', 'Blubuk', '2026-05-10 09:01:22');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','petugas') DEFAULT 'petugas',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`) VALUES
(1, 'admin', '123', 'admin', '2026-04-30 11:16:03'),
(2, 'petugas', '456', 'petugas', '2026-04-30 11:16:03');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `books`
--
ALTER TABLE `books`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `loans`
--
ALTER TABLE `loans`
  ADD PRIMARY KEY (`id`),
  ADD KEY `book_id` (`book_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `members`
--
ALTER TABLE `members`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `member_code` (`member_code`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `loans`
--
ALTER TABLE `loans`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `members`
--
ALTER TABLE `members`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `loans`
--
ALTER TABLE `loans`
  ADD CONSTRAINT `loans_ibfk_1` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`),
  ADD CONSTRAINT `loans_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;