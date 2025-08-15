import { forwardRef } from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'gradient' | 'success' | 'warning' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  rounded?: boolean;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    children,
    className = '',
    variant = 'primary',
    size = 'md',
    isLoading = false,
    disabled = false,
    icon,
    iconPosition = 'left',
    fullWidth = false,
    rounded = false,
    ...props
  }, ref) => {
    const baseStyles = `
      inline-flex items-center justify-center font-medium transition-all duration-300
      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-water-blue-500
      disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed
      transform hover:scale-105 active:scale-95
      ${rounded ? 'rounded-full' : 'rounded-lg'}
      ${fullWidth ? 'w-full' : ''}
    `;

    const variants = {
      primary: `
        bg-gradient-to-r from-water-blue-600 to-water-blue-700 text-white
        hover:from-water-blue-700 hover:to-water-blue-800
        shadow-lg hover:shadow-xl
        border border-water-blue-600 hover:border-water-blue-700
      `,
      secondary: `
        bg-gradient-to-r from-water-blue-100 to-water-blue-200 text-water-blue-800
        hover:from-water-blue-200 hover:to-water-blue-300
        shadow-md hover:shadow-lg
        border border-water-blue-200 hover:border-water-blue-300
      `,
      outline: `
        border-2 border-water-blue-500 text-water-blue-600 bg-transparent
        hover:bg-water-blue-50 hover:border-water-blue-600
        shadow-sm hover:shadow-md
      `,
      ghost: `
        text-water-blue-700 bg-transparent hover:bg-water-blue-50
        hover:text-water-blue-800
      `,
      gradient: `
        bg-gradient-to-r from-water-blue-500 via-ocean-500 to-aqua-500 text-white
        hover:from-water-blue-600 hover:via-ocean-600 hover:to-aqua-600
        shadow-lg hover:shadow-xl
        background-size: 200% 200%
        animate-gradient-shift
      `,
      success: `
        bg-gradient-to-r from-emerald-500 to-emerald-600 text-white
        hover:from-emerald-600 hover:to-emerald-700
        shadow-lg hover:shadow-xl
        border border-emerald-500 hover:border-emerald-600
      `,
      warning: `
        bg-gradient-to-r from-amber-500 to-amber-600 text-white
        hover:from-amber-600 hover:to-amber-700
        shadow-lg hover:shadow-xl
        border border-amber-500 hover:border-amber-600
      `,
      danger: `
        bg-gradient-to-r from-red-500 to-red-600 text-white
        hover:from-red-600 hover:to-red-700
        shadow-lg hover:shadow-xl
        border border-red-500 hover:border-red-600
      `,
    };

    const sizes = {
      xs: 'px-2 py-1 text-xs',
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
      xl: 'px-8 py-4 text-xl',
    };

    const LoadingSpinner = () => (
      <svg
        className="animate-spin h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <LoadingSpinner />
            <span className="ml-2">Loading...</span>
          </div>
        ) : (
          <div className="flex items-center justify-center">
            {icon && iconPosition === 'left' && (
              <span className={`${children ? 'mr-2' : ''}`}>{icon}</span>
            )}
            {children}
            {icon && iconPosition === 'right' && (
              <span className={`${children ? 'ml-2' : ''}`}>{icon}</span>
            )}
          </div>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
