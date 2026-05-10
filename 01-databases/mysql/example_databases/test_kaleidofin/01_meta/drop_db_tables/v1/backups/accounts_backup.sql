CREATE TABLE `accounts` (
  `id` bigint NOT NULL,
  `accountRef` varchar(255) NOT NULL,
  `accountTypeId` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `customerId` bigint NOT NULL,
  `fullDepositDate` date DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `sync_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id` (`id`),
  KEY `idx_createdAt` (`createdAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Backed up 40500 rows from accounts
