import { ReactNode } from 'react'
import { MdArrowUpward, MdArrowDownward, MdWarning } from 'react-icons/md'

interface KpiCardProps {
  title: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'warning'
  progress?: number
  icon: ReactNode
  className?: string
}

export default function KpiCard({ title, value, change, changeType, progress, icon, className = '' }: KpiCardProps) {
  return (
    <div className={`widget-card rounded-lg p-4 flex flex-col gap-1 ${className}`}>
      <div className="flex justify-between items-start">
        <span className="text-xs font-medium text-outline">{title}</span>
        <span className="text-secondary text-xl">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-on-surface">{value}</div>
      {change && (
        <div className={`flex items-center gap-1 text-xs ${
          changeType === 'positive' ? 'text-secondary' :
          changeType === 'negative' ? 'text-primary' :
          'text-error'
        }`}>
          {changeType === 'positive' && <MdArrowUpward />}
          {changeType === 'negative' && <MdArrowDownward />}
          {changeType === 'warning' && <MdWarning />}
          {change}
        </div>
      )}
      {progress !== undefined && (
        <div className="w-full h-1 bg-surface-variant rounded-full overflow-hidden mt-1">
          <div className="h-full bg-primary" style={{ width: `${progress}%` }}></div>
        </div>
      )}
    </div>
  )
}