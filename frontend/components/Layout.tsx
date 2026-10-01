'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Activity,
  Bot,
  ChevronRight,
  CircleHelp,
  LayoutDashboard,
  Menu,
  Settings,
  ShieldCheck,
  Stethoscope,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'

interface LayoutProps { children: ReactNode }

const navGroups = [
  {
    label: 'Clinical workspace',
    items: [
      { name: 'Overview', href: '/', icon: LayoutDashboard },
      { name: 'Patient registry', href: '/explorer', icon: Users },
      { name: 'AI clinical assistant', href: '/ai-agent', icon: Bot },
    ],
  },
  {
    label: 'Decision support',
    items: [
      { name: 'Model insights', href: '/explainability', icon: Activity },
      { name: 'System settings', href: '/settings', icon: Settings },
    ],
  },
]

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const current = navGroups.flatMap((group) => group.items).find((item) => item.href === pathname)
  const SidebarContent = () => (
    <>
      <div className="flex items-center justify-between px-3 pb-8">
        <Link href="/" onClick={() => setMobileOpen(false)} className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-teal-600 text-white shadow-lg shadow-teal-900/20"><Stethoscope aria-hidden="true" /></span>
          <span><span className="block text-base font-semibold tracking-tight text-slate-100">VitalOS</span><span className="block text-[11px] text-slate-400">Hospital operations</span></span>
        </Link>
        <button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X /></button>
      </div>
      <nav className="flex flex-col gap-7" aria-label="Primary navigation">
        {navGroups.map((group) => <div key={group.label}>
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{group.label}</p>
          <div className="flex flex-col gap-1">
            {group.items.map((item) => {
              const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
              const Icon = item.icon
              return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${active ? 'bg-teal-500/15 text-teal-300 ring-1 ring-inset ring-teal-500/20' : 'text-slate-400 hover:bg-slate-800/80 hover:text-slate-100'}`}>
                <Icon aria-hidden="true" className={active ? 'text-teal-300' : 'text-slate-500'} />
                <span className="flex-1">{item.name}</span>{active && <ChevronRight aria-hidden="true" className="text-teal-400" />}
              </Link>
            })}
          </div>
        </div>)}
      </nav>
      <div className="mt-auto pt-8">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-200"><ShieldCheck aria-hidden="true" className="text-emerald-400" /> Clinical workspace secure</div>
          <p className="mt-2 text-xs leading-5 text-slate-500">Connected to live hospital data services.</p>
        </div>
      </div>
    </>
  )

  return <div className="min-h-screen bg-slate-950 text-slate-100">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 flex-col border-r border-slate-800/80 bg-slate-950 px-5 py-6 lg:flex"><SidebarContent /></aside>
    {mobileOpen && <div className="fixed inset-0 z-50 bg-slate-950 lg:hidden"><aside className="flex h-full w-full max-w-sm flex-col border-r border-slate-800 bg-slate-950 px-5 py-6"><SidebarContent /></aside></div>}
    <div className="lg:pl-72">
      <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-slate-800/80 bg-slate-950/90 px-5 backdrop-blur-xl sm:px-8">
        <div className="flex items-center gap-3"><button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu /></button><div><p className="text-sm font-medium text-slate-100">{current?.name ?? 'Clinical workspace'}</p><p className="text-xs text-slate-500">Tuesday, October 2, 2026 <span className="mx-1 text-slate-700">·</span> Day shift</p></div></div>
        <div className="flex items-center gap-3"><button className="hidden rounded-lg p-2 text-slate-400 hover:bg-slate-800 sm:block" aria-label="Help"><CircleHelp /></button><div className="hidden h-8 w-px bg-slate-800 sm:block" /><div className="flex items-center gap-2"><div className="flex size-9 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-teal-300">JD</div><div className="hidden sm:block"><p className="text-xs font-medium text-slate-200">Jordan Davis</p><p className="text-[11px] text-slate-500">Operations lead</p></div></div></div>
      </header>
      <main className="mx-auto max-w-[1500px] px-5 py-7 sm:px-8 lg:px-10">{children}</main>
    </div>
  </div>
}
