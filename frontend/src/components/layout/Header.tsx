// components/layout/Header.tsx — top bar with page title

interface HeaderProps {
  title:    string
  subtitle?: string
  actions?:  React.ReactNode
}

export default function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface/80 backdrop-blur-sm relative z-10">
      <div>
        <h1 className="font-display text-snow font-semibold text-lg tracking-wide">{title}</h1>
        {subtitle && <p className="text-ghost text-xs font-mono mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
