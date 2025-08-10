import React from 'react';

interface BubbleProps {
  size: number;
  left: number;
  delay: number;
  duration: number;
}

const Bubble: React.FC<BubbleProps> = ({ size, left, delay, duration }) => (
  <div
    className="absolute bottom-0 rounded-full bg-gradient-to-t from-water-blue-300/60 to-water-blue-100/40 
      animate-bubble pointer-events-none backdrop-blur-sm"
    style={{
      width: `${size}px`,
      height: `${size}px`,
      left: `${left}%`,
      animationDelay: `${delay}s`,
      animationDuration: `${duration}s`,
      boxShadow: 'inset 0 0 10px rgba(255, 255, 255, 0.3), 0 2px 10px rgba(6, 188, 240, 0.2)'
    }}
  >
    <div 
      className="absolute top-2 left-2 w-2 h-2 bg-white/50 rounded-full blur-sm"
      style={{ width: `${size * 0.2}px`, height: `${size * 0.2}px` }}
    />
  </div>
);

interface WaterBubblesProps {
  count?: number;
  className?: string;
}

export const WaterBubbles: React.FC<WaterBubblesProps> = ({ 
  count = 8, 
  className = '' 
}) => {
  const bubbles = Array.from({ length: count }, (_, i) => ({
    id: i,
    size: Math.random() * 20 + 10,
    left: Math.random() * 90 + 5,
    delay: Math.random() * 3,
    duration: Math.random() * 2 + 3,
  }));

  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {bubbles.map((bubble) => (
        <Bubble
          key={bubble.id}
          size={bubble.size}
          left={bubble.left}
          delay={bubble.delay}
          duration={bubble.duration}
        />
      ))}
    </div>
  );
};
