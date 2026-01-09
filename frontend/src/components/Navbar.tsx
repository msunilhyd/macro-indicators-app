'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { Menu, X, TrendingUp, LogOut } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';

const categories = [
  { name: 'Market Indexes', slug: 'market-indexes' },
  { name: 'Precious Metals', slug: 'precious-metals' },
  { name: 'Energy', slug: 'energy' },
  { name: 'Commodities', slug: 'commodities' },
  { name: 'Exchange Rates', slug: 'exchange-rates' },
  { name: 'Interest Rates', slug: 'interest-rates' },
  { name: 'Economy', slug: 'economy' },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in as admin
    const token = localStorage.getItem('admin_token');
    setIsAdmin(!!token);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setIsAdmin(false);
    router.push('/admin');
  };

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="font-bold text-xl text-gray-800">MacroData</span>
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-1">
            {categories.map((cat) => (
              <Link
                key={cat.slug}
                href={`/category/${cat.slug}`}
                className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                {cat.name}
              </Link>
            ))}
            {isAdmin ? (
              <div className="ml-4 flex items-center gap-2 border-l border-gray-200 pl-4">
                <Link
                  href="/admin/dashboard"
                  className="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
                >
                  Admin Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors flex items-center gap-1"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            ) : (
              <Link
                href="/admin"
                className="ml-4 px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors border-l border-gray-200"
              >
                Admin
              </Link>
            )}
          </div>

          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {isOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {categories.map((cat) => (
              <Link
                key={cat.slug}
                href={`/category/${cat.slug}`}
                className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                onClick={() => setIsOpen(false)}
              >
                {cat.name}
              </Link>
            ))}
            {isAdmin ? (
              <>
                <Link
                  href="/admin/dashboard"
                  className="block px-3 py-2 text-base font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md"
                  onClick={() => setIsOpen(false)}
                >
                  Admin Dashboard
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-base font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                href="/admin"
                className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                onClick={() => setIsOpen(false)}
              >
                Admin
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
