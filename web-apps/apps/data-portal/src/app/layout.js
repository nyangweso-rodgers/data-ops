import "./globals.css";

export const metadata = {
  title: "Data Portal",
  description: "Browse and filter data-ops datasets",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
