import { useEffect, useState } from 'react';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  className?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'gradient';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  showGlow?: boolean;
  striped?: boolean;
}

export const ProgressBar = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  className = '',
  variant = 'default',
  size = 'md',
  animated = true,
  showGlow = false,
  striped = false,
}: ProgressBarProps) => {
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  useEffect(() => {
    // Animate progress bar with staggered effect
    const visibilityTimer = setTimeout(() => {
      setIsVisible(true);
    }, 50);

    const progressTimer = setTimeout(() => {
      setProgress(percentage);
    }, animated ? 200 : 0);

    return () => {
      clearTimeout(visibilityTimer);
      clearTimeout(progressTimer);
    };
  }, [percentage, animated]);

  const variants = {
    default: 'from-water-blue-400 to-water-blue-600',
    success: 'from-emerald-400 to-emerald-600',
    warning: 'from-amber-400 to-amber-600',
    danger: 'from-red-400 to-red-600',
    gradient: 'from-water-blue-400 via-ocean-500 to-aqua-500',
  };

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const getStatusColor = () => {
    if (percentage >= 90) return 'success';
    if (percentage >= 70) return 'default';
    if (percentage >= 40) return 'warning';
    return 'danger';
  };

  const statusVariant = variant === 'default' ? getStatusColor() : variant;

  return (
    <div className={`w-full ${animated ? 'animate-fade-in' : ''} ${className}`}>
      {label && (
        <div className={`flex justify-between text-sm mb-2 ${animated ? 'animate-slide-in-left' : ''}`}>
          <span className="font-medium text-gray-700 transition-colors duration-200 hover:text-gray-900">
            {label}
          </span>
          {showPercentage && (
            <span className={`font-medium transition-colors duration-200 ${
              statusVariant === 'success' ? 'text-emerald-700' :
              statusVariant === 'warning' ? 'text-amber-700' :
              statusVariant === 'danger' ? 'text-red-700' :
              'text-water-blue-700'
            }`}>
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}

      <div className={`
        w-full bg-gray-200 rounded-full overflow-hidden relative
        ${sizes[size]}
        ${showGlow ? 'shadow-lg' : 'shadow-sm'}
        ${animated ? 'animate-slide-in-right' : ''}
        transition-all duration-300
      `}>
        {/* Background pattern for striped effect */}
        {striped && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-water-flow" />
        )}

        {/* Progress bar */}
        <div
          className={`
            bg-gradient-to-r ${variants[statusVariant]} h-full rounded-full relative
            transition-all duration-1000 ease-out
            ${showGlow ? `shadow-lg shadow-${statusVariant === 'success' ? 'emerald' : statusVariant === 'warning' ? 'amber' : statusVariant === 'danger' ? 'red' : 'water-blue'}-500/50` : ''}
            ${animated ? 'animate-shimmer' : ''}
          `}
          style={{
            width: `${isVisible ? progress : 0}%`,
            backgroundSize: striped ? '20px 20px' : 'auto',
          }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-water-flow opacity-60" />

          {/* Glow effect */}
          {showGlow && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-smooth-pulse" />
          )}
        </div>
      </div>

      {/* Status indicator */}
      {percentage > 0 && (
        <div className={`mt-1 text-xs text-gray-500 ${animated ? 'animate-fade-in-up' : ''}`}>
          {percentage === 100 ? '✓ Complete' :
           percentage >= 90 ? '🎯 Nearly complete' :
           percentage >= 70 ? '⚡ Good progress' :
           percentage >= 40 ? '⚠️ In progress' :
           '🚀 Getting started'}
        </div>
      )}
    </div>
  );
};
