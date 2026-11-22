-- CreateTable
CREATE TABLE "participants_survey" (
    "id" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone_number" TEXT NOT NULL,
    "nationality" TEXT NOT NULL,
    "city" TEXT NOT NULL,
    "what_should_we_keep_doing" TEXT NOT NULL,
    "what_should_we_start_doing" TEXT NOT NULL,
    "what_should_we_stop_doing" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "created_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "updated_by" TEXT NOT NULL DEFAULT 'rodgerso65@gmail.com',
    "created_by_name" TEXT NOT NULL DEFAULT 'Survey Service',
    "updated_by_name" TEXT NOT NULL DEFAULT 'Survey Service',

    CONSTRAINT "participants_survey_pkey" PRIMARY KEY ("id")
);

