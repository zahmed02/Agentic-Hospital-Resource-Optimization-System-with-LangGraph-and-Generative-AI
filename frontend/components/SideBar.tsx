'use client'
import Link from 'next/link'
export default function SideBar(){return <aside className="legacy-panel"><nav><Link href="/">Overview</Link><Link href="/ai-agent">AI clinical assistant</Link><Link href="/explorer">Patient registry</Link></nav></aside>}
