import { Inter } from "next/font/google";
import { Trirong } from "next/font/google";

import "./styles/global.css";

const inter = Inter({ subsets: ["latin"] });
const trirong = Trirong({ subsets: ["latin"], weight: ["400"] });

export const metadata = {
  title: "Survey Next.js App",
  description: "Survey Next.js App Generated by create next app",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={trirong.className}>{children}</body>
    </html>
  );
}
