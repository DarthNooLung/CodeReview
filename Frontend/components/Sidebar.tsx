'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CodeReviewIcon } from './icons/CodeReviewIcon';
import { CodeFormatIcon } from './icons/CodeFormatIcon';

const menuItems = [
  { name: '코드 리뷰', path: '/code-review', icon: <CodeReviewIcon /> },
  { name: '코드 정렬', path: '/code-format', icon: <CodeFormatIcon /> },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-gray-100 p-4">
      <h2 className="text-xl font-bold mb-6">기능 메뉴</h2>
      <nav className="flex flex-col gap-2">
        {menuItems.map(({ name, path, icon }) => (
          <Link key={path} href={path}>
            <div className={`flex items-center gap-2 p-2 rounded hover:bg-gray-200 cursor-pointer ${
              pathname === path ? 'bg-gray-300 font-semibold' : ''
            }`}>
              {icon}
              <span>{name}</span>
            </div>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
