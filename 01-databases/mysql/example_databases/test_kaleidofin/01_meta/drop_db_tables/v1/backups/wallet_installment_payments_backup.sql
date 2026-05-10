CREATE TABLE `wallet_installment_payments` (
  `id` int NOT NULL,
  `accountId` int NOT NULL,
  `instalmentScheduleId` int NOT NULL,
  `ledgerEntryId` int NOT NULL,
  `paymentType` int NOT NULL,
  `amountPaid` decimal(11,2) NOT NULL,
  `amountRefunded` decimal(10,2) DEFAULT NULL,
  `paymentDate` datetime DEFAULT NULL,
  `refundDate` datetime DEFAULT NULL,
  `paymentId` int DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `sync_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id` (`id`),
  KEY `idx_paymentDate` (`paymentDate`),
  KEY `idx_accountId` (`accountId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Backed up 0 rows from wallet_installment_payments
