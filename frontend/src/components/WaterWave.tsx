import { useEffect, useRef } from 'react';

interface WaterWaveProps {
  className?: string;
  color?: string;
  blur?: number;
  opacity?: number;
  speed?: 'slow' | 'normal' | 'fast';
  variant?: 'wave' | 'ripple' | 'flow';
}

export const WaterWave = ({
  className = '',
  color = '#06bcf0',
  blur = 15,
  opacity = 0.3,
  speed = 'normal',
  variant = 'wave',
}: WaterWaveProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameId = useRef<number>();
  
  const speedMap = {
    slow: 0.005,
    normal: 0.01,
    fast: 0.02,
  };
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    let time = 0;
    const speedValue = speedMap[speed];
    
    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;
      ctx.scale(2, 2);
    };
    
    const drawWave = () => {
      if (!canvas || !ctx) return;
      
      const width = canvas.width / 2;
      const height = canvas.height / 2;
      
      ctx.clearRect(0, 0, width, height);
      
      if (variant === 'wave') {
        // Enhanced wave with multiple layers
        for (let layer = 0; layer < 3; layer++) {
          ctx.beginPath();
          ctx.moveTo(0, height / 2);
          
          const amplitude = 15 - layer * 4;
          const frequency = 0.02 + layer * 0.01;
          const phase = time + layer * Math.PI / 3;
          
          for (let x = 0; x < width; x++) {
            const y = Math.sin(x * frequency + phase) * amplitude + 
                     Math.sin(x * frequency * 0.5 + phase * 0.7) * amplitude * 0.3 + 
                     height / 2 + layer * 5;
            ctx.lineTo(x, y);
          }
          
          ctx.lineTo(width, height);
          ctx.lineTo(0, height);
          ctx.closePath();
          
          const gradient = ctx.createLinearGradient(0, 0, 0, height);
          const layerOpacity = (opacity / 3) * (3 - layer);
          gradient.addColorStop(0, `${color}${Math.round(layerOpacity * 255).toString(16).padStart(2, '0')}`);
          gradient.addColorStop(1, `${color}00`);
          
          ctx.fillStyle = gradient;
          ctx.fill();
        }
      } else if (variant === 'ripple') {
        // Concentric ripples
        const centerX = width / 2;
        const centerY = height / 2;
        
        for (let i = 0; i < 5; i++) {
          const radius = (time * 100 + i * 30) % 200;
          const rippleOpacity = Math.max(0, opacity * (1 - radius / 200));
          
          ctx.beginPath();
          ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
          ctx.strokeStyle = `${color}${Math.round(rippleOpacity * 255).toString(16).padStart(2, '0')}`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      } else if (variant === 'flow') {
        // Flowing particles
        for (let i = 0; i < 20; i++) {
          const x = ((time * 50 + i * 20) % (width + 50)) - 25;
          const y = height / 2 + Math.sin(time + i) * 20;
          const size = 3 + Math.sin(time + i) * 2;
          
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = `${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`;
          ctx.fill();
        }
      }
      
      time += speedValue;
      animationFrameId.current = requestAnimationFrame(drawWave);
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    drawWave();
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [color, blur, opacity, speed, variant]);
  
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="absolute bottom-0 left-0 w-full h-full pointer-events-none"
        style={{ filter: `blur(${blur}px)` }}
      />
    </div>
  );
};
