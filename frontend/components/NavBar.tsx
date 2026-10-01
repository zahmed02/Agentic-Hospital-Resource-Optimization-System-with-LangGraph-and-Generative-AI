'use client'
import Link from 'next/link'
export default function NavBar(){return <header className="legacy-panel"><Link href="/">VitalOS</Link><nav><Link href="/">Overview</Link><Link href="/explorer">Patient registry</Link><Link href="/ai-agent">AI clinical assistant</Link><Link href="/explainability">Model insights</Link><Link href="/settings">System settings</Link></nav></header>}
