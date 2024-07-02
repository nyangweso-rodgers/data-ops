import { Inter } from "next/font/google";

import "../app/styles/globals.css";
import layoutStyles from "../app/styles/layout.module.css";

const inter = Inter({ subsets: ["latin"] });

import HeaderPage from "./components/navigation/header/page.js";
import LeftSidebarPage from "./components/navigation/left-sidebar/page.js";

export const metadata = {
  title: "Next.js App Portal",
  description: "Next.js App Portal",
};

const RootLayout = ({ children }) => {
  return (
    <html lang="en">
      <body className={inter.className}>
        <HeaderPage />
        <div className={`${layoutStyles.layoutContainer}`}>
          <aside className={`${layoutStyles.leftSidebarContainer}`}>
            <LeftSidebarPage />
          </aside>
          <main className={`${layoutStyles.mainContainer}`}>{children}</main>
        </div>
      </body>
    </html>
  );
};

export default RootLayout;
