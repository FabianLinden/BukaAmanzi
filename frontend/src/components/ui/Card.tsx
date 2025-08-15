import { ReactNode, useState } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverEffect?: boolean;
  variant?: 'default' | 'elevated' | 'glass' | 'gradient' | 'minimal';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  animated?: boolean;
  onClick?: () => void;
}

export const Card = ({
  children,
  className = '',
  hoverEffect = false,
  variant = 'default',
  padding = 'md',
  rounded = 'xl',
  animated = true,
  onClick
}: CardProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const baseStyles = `
    transition-all duration-300 ease-out overflow-hidden
    ${animated ? 'animate-fade-in' : ''}
    ${onClick ? 'cursor-pointer' : ''}
  `;

  const variants = {
    default: `
      bg-gradient-to-br from-white to-water-blue-50/60
      border border-water-blue-200/50 shadow-md
      ${hoverEffect ? 'hover:shadow-xl hover:-translate-y-1 hover:border-water-blue-300/60' : ''}
    `,
    elevated: `
      bg-white shadow-lg border border-gray-200/50
      ${hoverEffect ? 'hover:shadow-2xl hover:-translate-y-2 hover:border-gray-300/60' : ''}
    `,
    glass: `
      bg-white/80 backdrop-blur-md border border-white/20 shadow-lg
      ${hoverEffect ? 'hover:bg-white/90 hover:shadow-xl hover:-translate-y-1' : ''}
    `,
    gradient: `
      bg-gradient-to-br from-water-blue-50 via-white to-ocean-50/30
      border border-water-blue-200/30 shadow-lg
      ${hoverEffect ? 'hover:shadow-xl hover:-translate-y-1 hover:from-water-blue-100 hover:to-ocean-100/50' : ''}
    `,
    minimal: `
      bg-white border border-gray-100 shadow-sm
      ${hoverEffect ? 'hover:shadow-md hover:border-gray-200' : ''}
    `,
  };

  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };

  const roundedStyles = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full',
  };

  return (
    <div
      className={`
        ${baseStyles}
        ${variants[variant]}
        ${roundedStyles[rounded]}
        ${isHovered && hoverEffect ? 'animate-gentle-bounce' : ''}
        ${className}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      <div className={paddingStyles[padding]}>
        {children}
      </div>
    </div>
  );
};

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  icon?: ReactNode;
  animated?: boolean;
}

export const CardHeader = ({
  title,
  subtitle,
  action,
  icon,
  animated = true
}: CardHeaderProps) => (
  <div className={`flex items-center justify-between mb-4 ${animated ? 'animate-slide-in-left' : ''}`}>
    <div className="flex items-center">
      {icon && (
        <div className="mr-3 p-2 bg-water-blue-100 rounded-lg">
          {icon}
        </div>
      )}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 hover:text-water-blue-800 transition-colors">
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-gray-500 mt-1 hover:text-gray-600 transition-colors">
            {subtitle}
          </p>
        )}
      </div>
    </div>
    {action && (
      <div className={animated ? 'animate-slide-in-right' : ''}>
        {action}
      </div>
    )}
  </div>
);

interface CardContentProps {
  children: ReactNode;
  className?: string;
  animated?: boolean;
}

export const CardContent = ({
  children,
  className = '',
  animated = true
}: CardContentProps) => (
  <div className={`${animated ? 'animate-fade-in-up' : ''} ${className}`}>
    {children}
  </div>
);

interface CardFooterProps {
  children: ReactNode;
  className?: string;
  animated?: boolean;
  variant?: 'default' | 'actions' | 'stats';
}

export const CardFooter = ({
  children,
  className = '',
  animated = true,
  variant = 'default'
}: CardFooterProps) => {
  const variants = {
    default: 'mt-6 pt-4 border-t border-water-blue-100/60',
    actions: 'mt-6 pt-4 border-t border-gray-200/60 flex justify-end space-x-3',
    stats: 'mt-4 pt-4 border-t border-water-blue-100/60 grid grid-cols-2 gap-4',
  };

  return (
    <div className={`${variants[variant]} ${animated ? 'animate-slide-up' : ''} ${className}`}>
      {children}
    </div>
  );
};
