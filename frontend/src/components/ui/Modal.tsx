import { ReactNode, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  animated?: boolean;
  className?: string;
}

export const Modal = ({
  isOpen,
  onClose,
  children,
  title,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  animated = true,
  className = '',
}: ModalProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setIsAnimating(true);
      document.body.style.overflow = 'hidden';
    } else {
      setIsAnimating(false);
      const timer = setTimeout(() => {
        setIsVisible(false);
        document.body.style.overflow = 'unset';
      }, animated ? 300 : 0);
      return () => clearTimeout(timer);
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, animated]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, closeOnEscape, onClose]);

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isVisible) return null;

  const modalContent = (
    <div
      className={`
        fixed inset-0 z-50 flex items-center justify-center p-4
        ${animated ? 'transition-all duration-300 ease-out' : ''}
        ${isAnimating ? 'animate-fade-in' : 'opacity-0'}
      `}
    >
      {/* Backdrop */}
      <div
        className={`
          absolute inset-0 bg-black/50 backdrop-blur-sm
          ${animated ? 'transition-opacity duration-300' : ''}
          ${isAnimating ? 'opacity-100' : 'opacity-0'}
        `}
        onClick={handleOverlayClick}
      />

      {/* Modal Content */}
      <div
        className={`
          relative bg-white rounded-xl shadow-2xl w-full ${sizes[size]}
          max-h-[90vh] overflow-hidden
          ${animated ? 'transition-all duration-300 ease-out' : ''}
          ${isAnimating ? 'animate-scale-in' : 'scale-95 opacity-0'}
          ${className}
        `}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            {title && (
              <h2 className="text-xl font-semibold text-gray-900 animate-fade-in-down">
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className={`
                  p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100
                  transition-all duration-200 transform hover:scale-110
                  ${animated ? 'animate-fade-in-down' : ''}
                `}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className={`
          p-6 overflow-y-auto max-h-[calc(90vh-8rem)]
          ${animated ? 'animate-fade-in-up' : ''}
        `}>
          {children}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

// Modal Header Component
interface ModalHeaderProps {
  children: ReactNode;
  className?: string;
}

export const ModalHeader = ({ children, className = '' }: ModalHeaderProps) => (
  <div className={`p-6 border-b border-gray-200 ${className}`}>
    {children}
  </div>
);

// Modal Body Component
interface ModalBodyProps {
  children: ReactNode;
  className?: string;
}

export const ModalBody = ({ children, className = '' }: ModalBodyProps) => (
  <div className={`p-6 ${className}`}>
    {children}
  </div>
);

// Modal Footer Component
interface ModalFooterProps {
  children: ReactNode;
  className?: string;
}

export const ModalFooter = ({ children, className = '' }: ModalFooterProps) => (
  <div className={`p-6 border-t border-gray-200 flex justify-end space-x-3 ${className}`}>
    {children}
  </div>
);
