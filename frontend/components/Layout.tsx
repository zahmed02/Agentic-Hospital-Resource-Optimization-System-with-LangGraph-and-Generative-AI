'use client'

import { ReactNode, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  FaDatabase, FaMicrochip, FaBrain, 
  FaNotesMedical, FaChartLine, FaUsers, 
  FaSignOutAlt, FaHeartbeat, FaBed, FaClock 
} from 'react-icons/fa'
import { MdWarning } from 'react-icons/md'

interface LayoutProps {
  children: ReactNode
}

const navLinks = [
  { name: 'Dashboard', href: '/', icon: 'FaHeartbeat' },
  { name: 'AI Agent', href: '/ai-agent', icon: 'FaBrain' },
  { name: 'Explorer', href: '/explorer', icon: 'FaUsers' },
  { name: 'Explainability', href: '/explainability', icon: 'FaChartLine' },
  { name: 'Settings', href: '/settings', icon: 'FaDatabase' },
]

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Fixed Header */}
      <motion.header
        className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-6 bg-surface-container/80 backdrop-blur-md border-b border-white/10 shadow-sm"
        initial={{ y: -60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 120, damping: 15, delay: 0.1 }}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-primary tracking-tight">VITAL_OS</span>
          <span className="text-xs text-on-surface-variant hidden sm:inline">v4.2.0</span>
        </div>
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-all duration-200 ${
                pathname === link.href
                  ? 'text-primary border-b-2 border-primary pb-1'
                  : 'text-on-surface-variant hover:text-primary hover:scale-105'
              }`}
            >
              {link.name}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
            <FaDatabase className="text-on-surface-variant" />
          </button>
          <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
            <FaMicrochip className="text-on-surface-variant" />
          </button>
          <button className="p-2 hover:bg-surface-variant rounded-full transition-colors">
            <FaBrain className="text-on-surface-variant" />
          </button>
          <div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center text-on-surface-variant text-sm border border-outline-variant">
            JD
          </div>
        </div>
      </motion.header>

      {/* Fixed Sidebar */}
      <motion.aside
        className="fixed left-0 top-16 bottom-0 z-40 w-64 bg-surface-container-low/80 backdrop-blur-sm border-r border-white/10 p-4 space-y-2 overflow-y-auto hidden lg:block"
        initial={{ x: -80, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 100, damping: 15, delay: 0.15 }}
      >
        <div className="mb-6 px-2">
          <p className="text-lg font-bold text-primary">VITAL_OS</p>
          <p className="text-xs text-on-surface-variant">Command Center</p>
        </div>
        <nav className="space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${
                pathname === link.href
                  ? 'bg-primary-container text-on-primary-container font-bold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:scale-105'
              }`}
            >
              <span className="material-symbols-outlined">{link.icon}</span>
              <span>{link.name}</span>
            </Link>
          ))}
        </nav>
        <div className="mt-auto pt-4 border-t border-white/10 space-y-1">
          <button className="w-full bg-error/20 text-error py-2 rounded-lg font-bold hover:bg-error/30 transition-colors">
            EMERGENCY
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <motion.main
        className="lg:ml-64 pt-20 px-4 md:px-8 pb-8 flex-1"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
      >
        <div className="max-w-7xl mx-auto bg-surface-container-low/50 backdrop-blur-sm rounded-xl p-4 md:p-6 border border-white/5">
          {children}
        </div>
      </motion.main>

      {/* Footer */}
      <motion.footer
        className="lg:ml-64 border-t border-white/10 bg-surface-container-highest/50 backdrop-blur-sm py-4 px-6"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-2 text-xs text-on-surface-variant">
          <span>© 2026 VITAL_OS – Secure Node Cluster 09</span>
          <div className="flex gap-4">
            <a href="#" className="hover:underline">System Logs</a>
            <a href="#" className="hover:underline">Privacy</a>
            <a href="#" className="hover:underline">Support</a>
          </div>
        </div>
      </motion.footer>
    </div>
  )
}