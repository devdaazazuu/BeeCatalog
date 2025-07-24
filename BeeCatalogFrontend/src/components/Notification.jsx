import React, { useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

const Notification = ({ type = 'info', title, message, onClose, autoClose = true, duration = 5000 }) => {
  useEffect(() => {
    if (autoClose && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <AlertCircle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-800/90 border-green-500 text-green-100';
      case 'error':
        return 'bg-red-800/90 border-red-500 text-red-100';
      case 'warning':
        return 'bg-yellow-800/90 border-yellow-500 text-yellow-100';
      default:
        return 'bg-blue-800/90 border-blue-500 text-blue-100';
    }
  };

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-md w-full mx-auto`}>
      <div className={`${getStyles()} border-l-4 p-4 rounded-lg shadow-lg backdrop-blur-sm`}>
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 flex-1">
            {title && (
              <h3 className="text-sm font-medium mb-1">
                {title}
              </h3>
            )}
            <p className="text-sm opacity-90">
              {message}
            </p>
          </div>
          {onClose && (
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={onClose}
                className="inline-flex text-current hover:opacity-75 focus:outline-none focus:opacity-75"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Notification;