'use client'

import Link from 'next/link'
import { FaNotesMedical, FaChartLine, FaUsers } from 'react-icons/fa'
import { MdWarning } from 'react-icons/md'

export default function SideBar() {
  return (
    <aside className="fixed left-0 top-16 bottom-0 z-40 w-64 bg-surface-container-high/90 backdrop-blur-md border-r border-white/5 shadow-xl flex flex-col py-6 px-4 gap-2 overflow-y-auto">
      <div className="px-2 pb-4 border-b border-white/10 mb-2">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-surface-variant flex items-center justify-center">
            <span className="text-secondary text-lg">⚕</span>
          </div>
          <div>
            <div className="text-sm font-semibold text-on-surface">Clinical Actions</div>
            <div className="text-[10px] uppercase text-secondary tracking-wider">AI Assisted</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 flex flex-col gap-2">
        <Link
          href="/"
          className="bg-secondary-container text-on-secondary-container rounded-lg p-3 flex items-center gap-3 transition-colors hover:bg-secondary-container/80"
        >
          <FaNotesMedical size={18} />
          <span className="text-sm font-medium">Ward Status</span>
        </Link>
        <Link
          href="/ai-agent"
          className="text-on-surface-variant hover:text-secondary p-3 rounded-lg hover:bg-surface-bright flex items-center gap-3 transition-colors"
        >
          <FaChartLine size={18} />
          <span className="text-sm font-medium">Predict LOS</span>
        </Link>
        <Link
          href="/explorer"
          className="text-on-surface-variant hover:text-secondary p-3 rounded-lg hover:bg-surface-bright flex items-center gap-3 transition-colors"
        >
          <FaUsers size={18} />
          <span className="text-sm font-medium">Find Similar</span>
        </Link>
      </nav>
      <div className="mt-auto pt-4 border-t border-white/10">
        <button className="w-full bg-error text-on-error text-sm font-bold py-2 rounded border border-error/50 hover:bg-error/80 transition-colors">
          EMERGENCY OVERRIDE
        </button>
        <div className="flex justify-center mt-2">
          <MdWarning className="text-error text-2xl" />
        </div>
      </div>
    </aside>
  )
}