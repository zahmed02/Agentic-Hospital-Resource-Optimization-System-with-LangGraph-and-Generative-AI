'use client'

import { useState } from 'react'
import { FaRobot, FaMicrophone, FaPaperPlane, FaBrain } from 'react-icons/fa'
import { queryAgent } from '@/lib/api'

const quickActions = ['Show ICU occupancy', 'Summarize shift notes', 'Flag abnormal vitals']

export default function AIAgentPage() {
  const [messages, setMessages] = useState<{ role: 'user' | 'agent'; content: string; time?: string; data?: any }[]>([
    { role: 'agent', content: 'Hello! I am your VITAL_OS Clinical Assistant. How can I help you today?', time: new Date().toLocaleTimeString() },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = input
    setMessages(prev => [...prev, { role: 'user', content: userMsg, time: new Date().toLocaleTimeString() }])
    setInput('')
    setLoading(true)
    try {
      const response = await queryAgent(userMsg)
      setMessages(prev => [...prev, { role: 'agent', content: response.response || 'No response', time: new Date().toLocaleTimeString() }])
    } catch (error: any) {
      setMessages(prev => [...prev, { role: 'agent', content: `Error: ${error.message}`, time: new Date().toLocaleTimeString() }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] min-h-[500px]">
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-surface-container-low/50 rounded-xl border border-white/5">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'agent' && (
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <FaRobot className="text-primary text-sm" />
              </div>
            )}
            <div className={`max-w-[80%] px-4 py-2 rounded-xl ${msg.role === 'user' ? 'bg-primary-container text-on-primary-container rounded-tr-none' : 'bg-surface-container-high text-on-surface rounded-tl-none'}`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.data && (
                <div className="mt-2 space-y-1 text-xs">
                  {msg.data.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between border-b border-white/5 py-1 last:border-0">
                      <span className="font-mono text-secondary">{item.id}</span>
                      <span>{item.condition}</span>
                      <span className={item.color}>{item.los}</span>
                    </div>
                  ))}
                </div>
              )}
              {msg.role === 'agent' && msg.content !== 'Loading...' && (
                <div className="mt-3 flex gap-2">
                  <button className="text-xs bg-surface-bright px-2 py-1 rounded border border-white/10 hover:bg-surface-variant transition">Explain</button>
                  <button className="text-xs bg-surface-bright px-2 py-1 rounded border border-white/10 hover:bg-surface-variant transition">Open in Explorer</button>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center shrink-0 text-on-surface-variant text-sm">
                U
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <FaRobot className="text-primary text-sm" />
            </div>
            <div className="bg-surface-container-high text-on-surface px-4 py-2 rounded-xl rounded-tl-none">
              <p className="text-sm">Thinking...</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4">
        <div className="flex flex-wrap gap-2 mb-3">
          {quickActions.map((action) => (
            <button
              key={action}
              onClick={() => {
                setInput(action)
                setTimeout(sendMessage, 100)
              }}
              className="px-3 py-1 rounded-full border border-secondary/30 text-secondary text-xs hover:bg-secondary/10 transition"
            >
              {action}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 bg-surface-container-high border border-white/10 rounded-lg px-3 py-1.5 focus-within:ring-2 focus-within:ring-primary/20">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && sendMessage()}
            className="flex-1 bg-transparent border-0 focus:ring-0 text-sm placeholder:text-on-surface-variant/50"
            placeholder="Ask VITAL_OS about patient data..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading} className="bg-primary text-on-primary p-1.5 rounded-lg hover:bg-primary/90 transition disabled:opacity-50">
            <FaPaperPlane size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}