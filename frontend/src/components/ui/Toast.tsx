// components/ui/Toast.tsx — lightweight inline alert

type ToastType = 'success' | 'error' | 'info'

interface ToastProps {
  message: string
  type?:   ToastType
  onDismiss?: () => void
}

const styles: Record<ToastType, string> = {
  success: 'border-arc/30 text-arc bg-arc/5',
  error:   'border-ember/30 text-ember bg-ember/5',
  info:    'border-pulse/30 text-pulse bg-pulse/5',
}

export default function Toast({ message, type = 'info', onDismiss }: ToastProps) {
  return (
    <div className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm font-body animate-fade-in ${styles[type]}`}>
      <span className="flex-1">{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="opacity-50 hover:opacity-100 transition-opacity ml-2 flex-shrink-0">✕</button>
      )}
    </div>
  )
}
