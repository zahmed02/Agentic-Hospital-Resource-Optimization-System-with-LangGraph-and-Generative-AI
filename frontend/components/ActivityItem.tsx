import { ReactNode } from 'react'
import { FaChartLine, FaExclamationTriangle, FaUserMd, FaSyncAlt } from 'react-icons/fa'

type IconMap = {
  [key: string]: ReactNode
}

const iconMap: IconMap = {
  analytics: <FaChartLine />,
  warning: <FaExclamationTriangle />,
  assignment_ind: <FaUserMd />,
  sync: <FaSyncAlt />,
}

interface ActivityItemProps {
  icon: string
  title: string
  desc: string
  time: string
  border: 'secondary' | 'error' | 'primary' | 'outline'
}

export default function ActivityItem({ icon, title, desc, time, border }: ActivityItemProps) {
  const borderColor = {
    secondary: 'border-secondary',
    error: 'border-error',
    primary: 'border-primary',
    outline: 'border-outline',
  }[border]

  const iconColor = {
    secondary: 'text-secondary',
    error: 'text-error',
    primary: 'text-primary',
    outline: 'text-outline',
  }[border]

  return (
    <div className={`flex gap-3 items-start p-2 hover:bg-white/5 rounded cursor-pointer transition-colors border-l-2 ${borderColor}`}>
      <span className={`text-sm mt-0.5 ${iconColor}`}>{iconMap[icon] || <FaChartLine />}</span>
      <div>
        <div className="text-xs font-medium text-on-surface">{title}</div>
        <div className="text-xs text-outline-variant">{desc}</div>
        <div className="text-[10px] text-outline mt-0.5">{time}</div>
      </div>
    </div>
  )
}