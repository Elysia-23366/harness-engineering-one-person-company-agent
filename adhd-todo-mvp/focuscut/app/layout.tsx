import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FocusCut - 任务拆解，一次一步',
  description: '专为 ADHD 用户设计的任务拆解工具，把大任务变成可执行的小步骤',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#0f172a',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <main className="mx-auto max-w-lg px-4 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}
