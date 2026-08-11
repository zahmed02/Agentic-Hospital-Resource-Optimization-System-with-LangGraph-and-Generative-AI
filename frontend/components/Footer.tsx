export default function Footer() {
  return (
    <footer className="bg-surface-container-lowest py-3 border-t border-white/5 ml-64">
      <div className="flex justify-between items-center px-6">
        <div className="text-xs text-outline">VITAL_OS v4.2.0-STABLE | SECURE NODE CLUSTER 09</div>
        <div className="flex gap-4 text-xs text-outline">
          <a href="#" className="hover:text-on-surface transition-colors">System Logs</a>
          <a href="#" className="hover:text-on-surface transition-colors">Privacy Protocol</a>
          <a href="#" className="hover:text-on-surface transition-colors">Tech Support</a>
        </div>
      </div>
    </footer>
  )
}