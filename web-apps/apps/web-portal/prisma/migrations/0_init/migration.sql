-- CreateEnum
CREATE TYPE "Status" AS ENUM ('TRUE', 'FALSE');

-- CreateTable
CREATE TABLE "user" (
    "id" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "status" "Status" NOT NULL DEFAULT 'TRUE',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "created_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "updated_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "created_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',
    "updated_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',

    CONSTRAINT "user_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "customer" (
    "id" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "status" "Status" NOT NULL DEFAULT 'TRUE',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "created_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "updated_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "created_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',
    "updated_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',

    CONSTRAINT "customer_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "delegates_survey" (
    "id" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "company_name" TEXT NOT NULL,
    "created_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "updated_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "created_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',
    "updated_by_name" TEXT NOT NULL DEFAULT 'Rodgers Nyangweso',

    CONSTRAINT "delegates_survey_pkey" PRIMARY KEY ("id")
);

