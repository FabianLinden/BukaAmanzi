import { forwardRef, InputHTMLAttributes, useState } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  variant?: 'default' | 'filled' | 'outlined' | 'minimal';
  inputSize?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  animated?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({
    label,
    error,
    helperText,
    icon,
    iconPosition = 'left',
    variant = 'default',
    inputSize = 'md',
    fullWidth = false,
    animated = true,
    className = '',
    ...props
  }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    const baseStyles = `
      transition-all duration-300 ease-out
      focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-transparent
      disabled:opacity-50 disabled:cursor-not-allowed
      ${fullWidth ? 'w-full' : ''}
      ${animated ? 'animate-fade-in' : ''}
    `;

    const variants = {
      default: `
        border border-gray-300 rounded-lg bg-white
        hover:border-water-blue-400 focus:border-water-blue-500
        ${isFocused ? 'shadow-lg' : 'shadow-sm'}
      `,
      filled: `
        border-0 rounded-lg bg-gray-100
        hover:bg-gray-200 focus:bg-white focus:shadow-lg
      `,
      outlined: `
        border-2 border-water-blue-300 rounded-lg bg-transparent
        hover:border-water-blue-400 focus:border-water-blue-600
        ${isFocused ? 'shadow-lg' : ''}
      `,
      minimal: `
        border-0 border-b-2 border-gray-300 rounded-none bg-transparent
        hover:border-water-blue-400 focus:border-water-blue-600
      `,
    };

    const sizes = {
      sm: 'px-3 py-2 text-sm',
      md: 'px-4 py-3 text-base',
      lg: 'px-5 py-4 text-lg',
    };

    const iconSizes = {
      sm: 'w-4 h-4',
      md: 'w-5 h-5',
      lg: 'w-6 h-6',
    };

    return (
      <div className={`${fullWidth ? 'w-full' : ''} ${animated ? 'animate-slide-up' : ''}`}>
        {label && (
          <label className={`
            block text-sm font-medium text-gray-700 mb-2
            ${animated ? 'animate-fade-in-down' : ''}
            ${isFocused ? 'text-water-blue-600' : ''}
            transition-colors duration-200
          `}>
            {label}
          </label>
        )}
        
        <div className="relative">
          {icon && iconPosition === 'left' && (
            <div className={`
              absolute left-3 top-1/2 transform -translate-y-1/2 
              text-gray-400 ${isFocused ? 'text-water-blue-500' : ''}
              transition-colors duration-200
            `}>
              <div className={iconSizes[inputSize]}>
                {icon}
              </div>
            </div>
          )}
          
          <input
            ref={ref}
            className={`
              ${baseStyles}
              ${variants[variant]}
              ${sizes[inputSize]}
              ${icon && iconPosition === 'left' ? 'pl-10' : ''}
              ${icon && iconPosition === 'right' ? 'pr-10' : ''}
              ${error ? 'border-red-500 focus:ring-red-500' : ''}
              ${className}
            `}
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            {...props}
          />
          
          {icon && iconPosition === 'right' && (
            <div className={`
              absolute right-3 top-1/2 transform -translate-y-1/2 
              text-gray-400 ${isFocused ? 'text-water-blue-500' : ''}
              transition-colors duration-200
            `}>
              <div className={iconSizes[inputSize]}>
                {icon}
              </div>
            </div>
          )}
        </div>
        
        {(error || helperText) && (
          <div className={`mt-2 ${animated ? 'animate-slide-down' : ''}`}>
            {error && (
              <p className="text-sm text-red-600 animate-fade-in">
                {error}
              </p>
            )}
            {helperText && !error && (
              <p className="text-sm text-gray-500">
                {helperText}
              </p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
