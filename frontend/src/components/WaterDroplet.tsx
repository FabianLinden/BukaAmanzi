import React from 'react';

interface WaterDropletProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  animated?: boolean;
  delay?: number;
}

export const WaterDroplet: React.FC<WaterDropletProps> = ({ 
  size = 'md', 
  className = '', 
  animated = true,
  delay = 0 
}) => {
  const sizeClasses = {
    sm: 'w-3 h-4',
    md: 'w-5 h-6',
    lg: 'w-8 h-10',
  };

  return (
    <div 
      className={`relative ${sizeClasses[size]} ${className}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div 
        className={`absolute inset-0 bg-gradient-to-b from-water-blue-200 to-water-blue-500 
          ${animated ? 'animate-droplet' : ''} shadow-lg`}
        style={{
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          filter: 'drop-shadow(0 2px 4px rgba(6, 188, 240, 0.3))'
        }}
      />
      <div 
        className="absolute top-1/4 left-1/4 w-1/3 h-1/3 bg-white/40 rounded-full blur-sm"
      />
    </div>
  );
};
