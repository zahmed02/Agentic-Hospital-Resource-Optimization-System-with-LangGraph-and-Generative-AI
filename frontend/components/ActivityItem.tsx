interface ActivityItemProps { title:string; desc:string; time:string; border:'secondary'|'error'|'primary'|'outline'; icon?:string }
export default function ActivityItem({title,desc,time,border}:ActivityItemProps){return <div className={`activity-row ${border}`}><div><strong>{title}</strong><p>{desc}</p><small>{time}</small></div></div>}
