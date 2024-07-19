import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";

const prisma = new PrismaClient();

export async function GET(req) {
  try {
    // Fetch all customers from the database
    const customers = await prisma.customer.findMany();
    return NextResponse.json(customers, { status: 200 });
  } catch (error) {
    console.log("Error fetching customers:", error);
    return NextResponse.json(
      { message: "Failed to fetch customers" },
      { status: 400 }
    );
  }
}