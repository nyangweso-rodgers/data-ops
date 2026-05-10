CREATE TABLE `customers` (
  `id` bigint NOT NULL,
  `companyRegionId` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `phoneNumber` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `walletID` varchar(255) DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `sync_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Backed up 0 rows from customers
