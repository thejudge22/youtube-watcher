interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

const gradientIds = {
  sm: 'gradient-sm',
  md: 'gradient-md',
  lg: 'gradient-lg',
};

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const gradientId = gradientIds[size];
  
  return (
    <div className={`relative ${sizeClasses[size]} ${className}`}>
      {/* Outer spinning ring */}
      <svg
        className="animate-spin w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ff3b30" />
            <stop offset="50%" stopColor="#bf5af2" />
            <stop offset="100%" stopColor="#0a84ff" />
          </linearGradient>
        </defs>
        <circle
          className="opacity-10"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
        />
        <path
          fill={`url(#${gradientId})`}
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}
