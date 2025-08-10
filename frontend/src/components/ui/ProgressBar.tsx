import { useEffect, useState } from 'react';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  className?: string;
}

export const ProgressBar = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  className = '',
}: ProgressBarProps) => {
  const [progress, setProgress] = useState(0);
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  useEffect(() => {
    // Animate progress bar
    const timer = setTimeout(() => {
      setProgress(percentage);
    }, 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium text-gray-700">{label}</span>
          {showPercentage && (
            <span className="font-medium text-water-blue-700">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <div 
          className="bg-gradient-to-r from-water-blue-400 to-water-blue-600 h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${progress}%`,
            backgroundImage: 'linear-gradient(90deg, #38bdf8 0%, #0284c7 100%)',
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white opacity-20 animate-water-shimmer"></div>
        </div>
      </div>
      <style jsx>{`
        @keyframes water-shimmer {
          0% { transform: translateX(-100%) rotate(0deg); }
          100% { transform: translateX(100%) rotate(0deg); }
        }
        .animate-water-shimmer {
          animation: water-shimmer 2s infinite linear;
        }
      `}</style>
    </div>
  );
};
