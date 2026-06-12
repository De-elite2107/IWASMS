import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        background: {
          body: '#0D1117',
          card: '#161B22',
          elevated: '#1C2128',
          border: '#30363D',
        },
        text: {
          primary: '#E6EDF3',
          secondary: '#8B949E',
          muted: '#6E7681',
        },
        threat: {
          critical: '#F85149',
          high: '#E3B341',
          medium: '#58A6FF',
          low: '#3FB950',
          none: '#3FB950',
          normal: '#3FB950',
        },
        accent: {
          primary: '#58A6FF',
          dim: '#1F6FEB',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
        sans: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '2px',
        sm: '2px',
        md: '2px',
        lg: '2px',
        xl: '2px',
      },
    },
  },
  plugins: [],
}

export default config
