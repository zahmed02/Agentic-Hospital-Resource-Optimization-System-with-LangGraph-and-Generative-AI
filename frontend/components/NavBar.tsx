'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FaDatabase, FaMicrochip, FaBrain } from 'react-icons/fa'

const navLinks = [
  { name: 'Dashboard', href: '/' },
  { name: 'AI Agent', href: '/ai-agent' },
  { name: 'Explorer', href: '/explorer' },
  { name: 'Explainability', href: '/explainability' },
  { name: 'Settings', href: '/settings' },
]

export default function NavBar() {
  const pathname = usePathname()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-surface-container dark:bg-surface-container/80 backdrop-blur-xl border-b border-white/10 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-primary tracking-tight">VITAL_OS</h1>
      </div>
      <nav className="hidden md:flex items-center gap-6 h-full">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`${
              pathname === link.href
                ? 'text-primary font-bold border-b-2 border-primary'
                : 'text-on-surface-variant font-medium hover:text-secondary-fixed'
            } pb-1 transition-colors duration-200 h-full flex items-center`}
          >
            {link.name}
          </Link>
        ))}
      </nav>
      <div className="flex items-center gap-3 text-primary">
        <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
          <FaDatabase size={20} />
        </button>
        <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
          <FaMicrochip size={20} />
        </button>
        <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
          <FaBrain size={20} />
        </button>
        <div className="w-9 h-9 rounded-full border border-outline overflow-hidden ml-2 bg-surface-variant flex items-center justify-center text-on-surface-variant text-sm">
          <span>CMO</span>
        </div>
      </div>
    </header>
  )
}