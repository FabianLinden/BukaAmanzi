import { ReactNode, useState, useRef, useEffect } from 'react';

interface TooltipProps {
  children: ReactNode;
  content: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus';
  delay?: number;
  className?: string;
  animated?: boolean;
  arrow?: boolean;
}

export const Tooltip = ({
  children,
  content,
  position = 'top',
  trigger = 'hover',
  delay = 200,
  className = '',
  animated = true,
  arrow = true,
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      setIsAnimating(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsAnimating(false);
    setTimeout(() => {
      setIsVisible(false);
    }, animated ? 150 : 0);
  };

  const handleMouseEnter = () => {
    if (trigger === 'hover') showTooltip();
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover') hideTooltip();
  };

  const handleClick = () => {
    if (trigger === 'click') {
      isVisible ? hideTooltip() : showTooltip();
    }
  };

  const handleFocus = () => {
    if (trigger === 'focus') showTooltip();
  };

  const handleBlur = () => {
    if (trigger === 'focus') hideTooltip();
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900',
    left: 'left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900',
    right: 'right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900',
  };

  const animationClasses = {
    top: isAnimating ? 'animate-fade-in-down' : 'opacity-0 translate-y-1',
    bottom: isAnimating ? 'animate-fade-in-up' : 'opacity-0 -translate-y-1',
    left: isAnimating ? 'animate-slide-in-right' : 'opacity-0 translate-x-1',
    right: isAnimating ? 'animate-slide-in-left' : 'opacity-0 -translate-x-1',
  };

  return (
    <div className="relative inline-block">
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="cursor-pointer"
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={`
            absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg
            max-w-xs break-words
            ${positionClasses[position]}
            ${animated ? animationClasses[position] : ''}
            ${className}
          `}
          style={{
            transition: animated ? 'all 0.15s ease-out' : 'none',
          }}
        >
          {content}
          
          {arrow && (
            <div
              className={`
                absolute w-0 h-0 border-4
                ${arrowClasses[position]}
              `}
            />
          )}
        </div>
      )}
    </div>
  );
};

// Quick tooltip variants
export const InfoTooltip = ({ children, content }: { children: ReactNode; content: ReactNode }) => (
  <Tooltip content={content} position="top" className="bg-water-blue-600">
    {children}
  </Tooltip>
);

export const WarningTooltip = ({ children, content }: { children: ReactNode; content: ReactNode }) => (
  <Tooltip content={content} position="top" className="bg-amber-600">
    {children}
  </Tooltip>
);

export const ErrorTooltip = ({ children, content }: { children: ReactNode; content: ReactNode }) => (
  <Tooltip content={content} position="top" className="bg-red-600">
    {children}
  </Tooltip>
);

export const SuccessTooltip = ({ children, content }: { children: ReactNode; content: ReactNode }) => (
  <Tooltip content={content} position="top" className="bg-emerald-600">
    {children}
  </Tooltip>
);
