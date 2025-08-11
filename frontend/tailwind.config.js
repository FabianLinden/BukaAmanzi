/** @type {import('tailwindcss').Config} */
const { fontFamily } = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', ...fontFamily.sans],
      },
      colors: {
        'water-blue': {
          50: '#f0fdff',
          100: '#d9f8ff',
          200: '#b8f2ff',
          300: '#87eaff',
          400: '#4dd7ff',
          500: '#06bcf0',
          600: '#0098d1',
          700: '#0078aa',
          800: '#05648c',
          900: '#0a5473',
        },
        'ocean': {
          50: '#f0fbff',
          100: '#e0f7fe',
          200: '#bef0fd',
          300: '#7ce0fc',
          400: '#32ccf8',
          500: '#08b6e9',
          600: '#0093c7',
          700: '#0176a1',
          800: '#066085',
          900: '#0b516f',
        },
        'aqua': {
          50: '#f0feff',
          100: '#cbfeff',
          200: '#9df9ff',
          300: '#59f1ff',
          400: '#0ee0f5',
          500: '#00c4d7',
          600: '#009db4',
          700: '#077d92',
          800: '#0e6577',
          900: '#125565',
        },
        'teal': {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },
      animation: {
        'water-ripple': 'ripple 3s cubic-bezier(0, 0.2, 0.8, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'bubble': 'bubble 4s ease-in-out infinite',
        'wave': 'wave 4s ease-in-out infinite',
        'flow': 'flow 8s ease-in-out infinite',
        'droplet': 'droplet 2s ease-in-out infinite',
        'shimmer': 'shimmer 3s ease-in-out infinite',
        'tide': 'tide 6s ease-in-out infinite',
        'splash': 'splash 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'card-float': 'cardFloat 4s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        ripple: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.7' },
          '50%': { transform: 'scale(1.05)', opacity: '0.5' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        bubble: {
          '0%, 100%': { transform: 'translateY(0) scale(1)', opacity: '0.7' },
          '50%': { transform: 'translateY(-20px) scale(1.1)', opacity: '0.9' },
        },
        wave: {
          '0%, 100%': { transform: 'translateX(-100%) skewX(0deg)' },
          '25%': { transform: 'translateX(-50%) skewX(2deg)' },
          '50%': { transform: 'translateX(0%) skewX(0deg)' },
          '75%': { transform: 'translateX(50%) skewX(-2deg)' },
        },
        flow: {
          '0%, 100%': { backgroundPosition: '0% 0%' },
          '50%': { backgroundPosition: '100% 100%' },
        },
        droplet: {
          '0%, 100%': { 
            transform: 'translateY(0) scale(1)',
            borderRadius: '50% 50% 50% 50%',
            opacity: '1'
          },
          '25%': {
            transform: 'translateY(-5px) scale(1.1)',
            borderRadius: '60% 40% 60% 40%'
          },
          '50%': { 
            transform: 'translateY(0) scale(1.05)',
            borderRadius: '50% 50% 60% 40%'
          },
          '75%': {
            transform: 'translateY(2px) scale(0.95)',
            borderRadius: '40% 60% 40% 60%'
          },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        tide: {
          '0%, 100%': { 
            transform: 'translateY(0px) rotate(0deg)',
            opacity: '0.6' 
          },
          '50%': { 
            transform: 'translateY(-15px) rotate(1deg)',
            opacity: '0.8' 
          },
        },
        splash: {
          '0%': { 
            transform: 'scale(0) rotate(0deg)',
            opacity: '1'
          },
          '50%': {
            transform: 'scale(1.2) rotate(180deg)',
            opacity: '0.8'
          },
          '100%': { 
            transform: 'scale(1) rotate(360deg)',
            opacity: '0'
          },
        },
        cardFloat: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '33%': { transform: 'translateY(-5px) rotate(0.5deg)' },
          '66%': { transform: 'translateY(-2px) rotate(-0.5deg)' },
        },
        glowPulse: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(6, 188, 240, 0.3), 0 0 40px rgba(6, 188, 240, 0.1)'
          },
          '50%': { 
            boxShadow: '0 0 30px rgba(6, 188, 240, 0.5), 0 0 60px rgba(6, 188, 240, 0.2)'
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}