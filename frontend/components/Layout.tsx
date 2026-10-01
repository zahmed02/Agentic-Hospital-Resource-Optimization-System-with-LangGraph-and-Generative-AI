'use client'

import { ReactNode, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface LayoutProps { children: ReactNode }

const navGroups = [
  { label: 'Care coordination', items: [{ name: 'Overview', href: '/' }, { name: 'Patient registry', href: '/explorer' }, { name: 'AI clinical assistant', href: '/ai-agent' }] },
  { label: 'Clinical intelligence', items: [{ name: 'Model insights', href: '/explainability' }, { name: 'System settings', href: '/settings' }] },
]

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const current = navGroups.flatMap((group) => group.items).find((item) => item.href === pathname)
  const navigation = <>
    <div className="brand-block">
      <Link href="/" onClick={() => setMobileOpen(false)} className="brand-link">
        <span><strong>VitalOS</strong><small>Hospital operations</small></span>
      </Link>
      <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation">Close</button>
    </div>
    <nav className="primary-nav" aria-label="Primary navigation">
      {navGroups.map((group) => <div className="nav-group" key={group.label}>
        <p>{group.label}</p>
        {group.items.map((item) => {
          const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
          return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={active ? 'nav-link active' : 'nav-link'}><span>{item.name}</span>{active && <b>Current</b>}</Link>
        })}
      </div>)}
    </nav>
    <div className="sidebar-status"><span>Workspace status</span><strong>Connected</strong><p>Hospital data services are available for this workspace.</p></div>
  </>
  return <div className="app-shell">
    <aside className="sidebar desktop-sidebar">{navigation}</aside>
    {mobileOpen && <div className="mobile-nav"><aside className="sidebar">{navigation}</aside></div>}
    <div className="content-shell">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation">Menu</button><div><p className="eyebrow">VitalOS / {current?.name ?? 'Clinical workspace'}</p><p className="date-line">Tuesday, October 2, 2026 <span>Day shift</span></p></div></div><div className="account"><span className="account-initials">JD</span><span><strong>Jordan Davis</strong><small>Operations lead</small></span></div></header>
      <main className="page-content">{children}</main>
    </div>
  </div>
}

export { navGroups }
