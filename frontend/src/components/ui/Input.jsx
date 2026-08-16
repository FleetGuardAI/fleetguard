import React from 'react';
import { cn } from '@/utils/cn';
import { ChevronDown } from 'lucide-react';

export const Input = React.forwardRef(
  ({ className, label, error, helperText, icon, iconRight, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-content-secondary">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-content-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full h-10 px-3 rounded-lg border bg-surface text-content text-sm',
              'transition-all duration-200',
              'placeholder:text-content-muted',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              icon && 'pl-10',
              iconRight && 'pr-10',
              error ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500' : 'border-border',
              className
            )}
            {...props}
          />
          {iconRight && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-content-muted">
              {iconRight}
            </div>
          )}
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
        {helperText && !error && <p className="text-xs text-content-muted">{helperText}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export const TextArea = React.forwardRef(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-content-secondary">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'w-full px-3 py-2.5 rounded-lg border bg-surface text-content text-sm min-h-[100px] resize-y',
            'transition-all duration-200 placeholder:text-content-muted',
            'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
            error ? 'border-red-500' : 'border-border',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);
TextArea.displayName = 'TextArea';

export const Select = React.forwardRef(
  ({ className, label, error, options, placeholder, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-content-secondary">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={inputId}
            className={cn(
              'w-full h-10 pl-3 pr-10 rounded-lg border bg-surface text-content text-sm appearance-none',
              'transition-all duration-200 cursor-pointer',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
              error ? 'border-red-500' : 'border-border',
              className
            )}
            {...props}
          >
            {placeholder && <option value="">{placeholder}</option>}
            {options.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-content-muted">
            <ChevronDown className="h-4 w-4" />
          </div>
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);
Select.displayName = 'Select';
