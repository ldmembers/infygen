// components/ui/Badge.tsx — source type badge

interface BadgeProps {
  label: string
}

const SOURCE_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  email:  { bg: 'rgba(244,128,74,0.1)',  text: '#f4804a', dot: '#f4804a' },
  pdf:    { bg: 'rgba(107,140,255,0.1)', text: '#6b8cff', dot: '#6b8cff' },
  csv:    { bg: 'rgba(74,244,200,0.1)',  text: '#4af4c8', dot: '#4af4c8' },
  txt:    { bg: 'rgba(74,244,200,0.08)', text: '#4af4c8', dot: '#4af4c8' },
  memory: { bg: 'rgba(255,200,100,0.1)', text: '#ffc864', dot: '#ffc864' },
}

const DEFAULT_STYLE = { bg: 'rgba(136,146,164,0.1)', text: '#8892a4', dot: '#8892a4' }

export default function Badge({ label }: BadgeProps) {
  const s = SOURCE_STYLES[label.toLowerCase()] ?? DEFAULT_STYLE
  return (
    <span
      className="source-tag font-mono"
      style={{ background: s.bg, color: s.text, border: `1px solid ${s.dot}33` }}
    >
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: s.dot, display: 'inline-block' }} />
      {label}
    </span>
  )
}
