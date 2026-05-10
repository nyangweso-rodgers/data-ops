CREATE TABLE `installment_schedules` (
  `id` int NOT NULL,
  `accountId` int NOT NULL,
  `customerId` int DEFAULT NULL,
  `installmentType` varchar(255) NOT NULL,
  `paymentSequence` int NOT NULL,
  `expectedAmount` int NOT NULL,
  `expectedDate` date DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` timestamp NOT NULL,
  `sync_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Backed up 0 rows from installment_schedules
