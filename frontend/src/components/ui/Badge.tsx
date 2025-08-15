import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  rounded?: boolean;
  animated?: boolean;
  icon?: ReactNode;
  className?: string;
  pulse?: boolean;
}

export const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  rounded = false,
  animated = true,
  icon,
  className = '',
  pulse = false,
}: BadgeProps) => {
  const baseStyles = `
    inline-flex items-center font-medium transition-all duration-200
    ${rounded ? 'rounded-full' : 'rounded-lg'}
    ${animated ? 'animate-fade-in' : ''}
    ${pulse ? 'animate-smooth-pulse' : ''}
  `;

  const variants = {
    default: `
      bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800
      border border-gray-300
    `,
    success: `
      bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800
      border border-emerald-300
    `,
    warning: `
      bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800
      border border-amber-300
    `,
    danger: `
      bg-gradient-to-r from-red-100 to-red-200 text-red-800
      border border-red-300
    `,
    info: `
      bg-gradient-to-r from-water-blue-100 to-water-blue-200 text-water-blue-800
      border border-water-blue-300
    `,
    secondary: `
      bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800
      border border-purple-300
    `,
  };

  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={`
        ${baseStyles}
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {icon && (
        <span className={`${iconSizes[size]} ${children ? 'mr-1.5' : ''}`}>
          {icon}
        </span>
      )}
      {children}
    </span>
  );
};

// Status Badge Component for project statuses
interface StatusBadgeProps {
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  animated?: boolean;
  showIcon?: boolean;
}

export const StatusBadge = ({ 
  status, 
  animated = true, 
  showIcon = true 
}: StatusBadgeProps) => {
  const statusConfig = {
    planned: {
      variant: 'info' as const,
      label: 'Planned',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    in_progress: {
      variant: 'warning' as const,
      label: 'In Progress',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      pulse: true,
    },
    completed: {
      variant: 'success' as const,
      label: 'Completed',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ),
    },
    delayed: {
      variant: 'danger' as const,
      label: 'Delayed',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      ),
      pulse: true,
    },
    cancelled: {
      variant: 'secondary' as const,
      label: 'Cancelled',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
    },
  };

  const config = statusConfig[status];

  return (
    <Badge
      variant={config.variant}
      animated={animated}
      icon={showIcon ? config.icon : undefined}
      pulse={config.pulse}
      rounded
    >
      {config.label}
    </Badge>
  );
};

// Priority Badge Component
interface PriorityBadgeProps {
  priority: 'low' | 'medium' | 'high' | 'critical';
  animated?: boolean;
}

export const PriorityBadge = ({ priority, animated = true }: PriorityBadgeProps) => {
  const priorityConfig = {
    low: { variant: 'secondary' as const, label: 'Low' },
    medium: { variant: 'info' as const, label: 'Medium' },
    high: { variant: 'warning' as const, label: 'High' },
    critical: { variant: 'danger' as const, label: 'Critical', pulse: true },
  };

  const config = priorityConfig[priority];

  return (
    <Badge
      variant={config.variant}
      animated={animated}
      pulse={config.pulse}
      size="sm"
    >
      {config.label}
    </Badge>
  );
};
