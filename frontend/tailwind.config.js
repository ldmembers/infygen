/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
        body:    ['"Instrument Sans"', 'sans-serif'],
      },
      colors: {
        // Core dark palette
        void:    '#07080a',
        surface: '#0d0f12',
        panel:   '#12151a',
        border:  '#1e2229',
        muted:   '#2a2f3a',
        // Accent system
        arc:     '#4af4c8',   // teal-green primary accent
        arcDim:  '#1a6b56',
        ember:   '#f4804a',   // warm orange for warnings/memory
        pulse:   '#6b8cff',   // blue for AI responses
        ghost:   '#8892a4',   // secondary text
        pale:    '#c5ccd8',   // primary text
        snow:    '#eef1f5',   // headings
      },
      animation: {
        'fade-up':    'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'scan':       'scan 3s linear infinite',
        'pulse-arc':  'pulseArc 2s ease-in-out infinite',
        'dot-blink':  'dotBlink 1.4s ease-in-out infinite',
        'slide-in':   'slideIn 0.35s cubic-bezier(0.16,1,0.3,1) forwards',
        'shimmer':    'shimmer 1.8s linear infinite',
      },
      keyframes: {
        fadeUp:   { '0%': { opacity:'0', transform:'translateY(16px)' }, '100%': { opacity:'1', transform:'translateY(0)' } },
        fadeIn:   { '0%': { opacity:'0' }, '100%': { opacity:'1' } },
        scan:     { '0%': { transform:'translateY(-100%)' }, '100%': { transform:'translateY(200%)' } },
        pulseArc: { '0%,100%': { boxShadow:'0 0 0 0 rgba(74,244,200,0.15)' }, '50%': { boxShadow:'0 0 0 8px rgba(74,244,200,0)' } },
        dotBlink: { '0%,80%,100%': { transform:'scale(0)', opacity:'0.2' }, '40%': { transform:'scale(1)', opacity:'1' } },
        slideIn:  { '0%': { opacity:'0', transform:'translateX(-12px)' }, '100%': { opacity:'1', transform:'translateX(0)' } },
        shimmer:  { '0%': { backgroundPosition:'-200% center' }, '100%': { backgroundPosition:'200% center' } },
      },
      backgroundImage: {
        'grid-lines': 'linear-gradient(rgba(74,244,200,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(74,244,200,0.03) 1px,transparent 1px)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
    },
  },
  plugins: [],
}
