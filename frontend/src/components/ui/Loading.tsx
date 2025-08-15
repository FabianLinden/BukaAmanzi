import { ReactNode } from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave' | 'water';
  color?: 'primary' | 'secondary' | 'white' | 'gray';
  text?: string;
  fullScreen?: boolean;
  overlay?: boolean;
  className?: string;
}

export const Loading = ({
  size = 'md',
  variant = 'spinner',
  color = 'primary',
  text,
  fullScreen = false,
  overlay = false,
  className = '',
}: LoadingProps) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const colors = {
    primary: 'text-water-blue-600',
    secondary: 'text-gray-600',
    white: 'text-white',
    gray: 'text-gray-400',
  };

  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  const SpinnerLoader = () => (
    <svg
      className={`animate-spin ${sizes[size]} ${colors[color]}`}
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

  const DotsLoader = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`
            ${size === 'sm' ? 'w-2 h-2' : size === 'md' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-5 h-5'}
            bg-current rounded-full animate-bounce
            ${colors[color]}
          `}
          style={{
            animationDelay: `${i * 0.1}s`,
            animationDuration: '0.6s',
          }}
        />
      ))}
    </div>
  );

  const PulseLoader = () => (
    <div
      className={`
        ${sizes[size]} ${colors[color]} bg-current rounded-full animate-smooth-pulse
      `}
    />
  );

  const WaveLoader = () => (
    <div className="flex items-end space-x-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`
            ${size === 'sm' ? 'w-1' : size === 'md' ? 'w-1.5' : size === 'lg' ? 'w-2' : 'w-3'}
            bg-current animate-wave
            ${colors[color]}
          `}
          style={{
            height: size === 'sm' ? '16px' : size === 'md' ? '24px' : size === 'lg' ? '32px' : '40px',
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );

  const WaterLoader = () => (
    <div className="relative">
      <div
        className={`
          ${sizes[size]} border-4 border-water-blue-200 rounded-full
          animate-spin
        `}
      />
      <div
        className={`
          absolute inset-2 bg-gradient-to-t from-water-blue-400 to-water-blue-600
          rounded-full animate-water-flow
        `}
      />
      <div
        className={`
          absolute inset-1 border-2 border-water-blue-300 rounded-full
          animate-pulse
        `}
      />
    </div>
  );

  const renderLoader = () => {
    switch (variant) {
      case 'dots':
        return <DotsLoader />;
      case 'pulse':
        return <PulseLoader />;
      case 'wave':
        return <WaveLoader />;
      case 'water':
        return <WaterLoader />;
      default:
        return <SpinnerLoader />;
    }
  };

  const content = (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      <div className="animate-fade-in">
        {renderLoader()}
      </div>
      {text && (
        <div className={`${textSizes[size]} ${colors[color]} font-medium animate-fade-in-up`}>
          {text}
        </div>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white">
        {content}
      </div>
    );
  }

  if (overlay) {
    return (
      <div className="absolute inset-0 z-40 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
};

// Skeleton Loader Component
interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  animated?: boolean;
  variant?: 'text' | 'rectangular' | 'circular';
}

export const Skeleton = ({
  width = '100%',
  height = '1rem',
  className = '',
  animated = true,
  variant = 'rectangular',
}: SkeletonProps) => {
  const baseClasses = `
    bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200
    ${animated ? 'animate-shimmer' : ''}
    background-size: 200% 100%
  `;

  const variants = {
    text: 'rounded',
    rectangular: 'rounded-md',
    circular: 'rounded-full',
  };

  return (
    <div
      className={`${baseClasses} ${variants[variant]} ${className}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  );
};

// Loading Overlay Component
interface LoadingOverlayProps {
  isLoading: boolean;
  children: ReactNode;
  loadingText?: string;
  variant?: LoadingProps['variant'];
}

export const LoadingOverlay = ({
  isLoading,
  children,
  loadingText = 'Loading...',
  variant = 'water',
}: LoadingOverlayProps) => {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <Loading
          variant={variant}
          text={loadingText}
          overlay
          size="lg"
          className="animate-fade-in"
        />
      )}
    </div>
  );
};
