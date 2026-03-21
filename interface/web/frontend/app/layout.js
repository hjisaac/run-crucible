import "./globals.css";

export const metadata = {
  title: "Crucible · Web Interface",
  description: "Monitor and trigger crucible runs from the browser.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
