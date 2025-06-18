import "@/styles/globals.css";
import Sidebar from '@/components/Sidebar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="flex">
        <Sidebar />
        <main className="flex-1 pt-0 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
