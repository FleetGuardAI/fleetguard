import { cn } from '@/utils/cn';

const variants = {
  success: 'bg-green-50 text-green-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-red-50 text-red-700',
  info: 'bg-blue-50 text-blue-700',
  neutral: 'bg-gray-100 text-gray-600',
  brand: 'bg-brand-50 text-brand-700',
};

export function Badge({ variant = 'neutral', size = 'sm', dot, children, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full whitespace-nowrap',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        variants[variant],
        className
      )}
    >
      {dot && (
        <span className={cn('w-1.5 h-1.5 rounded-full', {
          'bg-green-500': variant === 'success',
          'bg-amber-500': variant === 'warning',
          'bg-red-500': variant === 'danger',
          'bg-blue-500': variant === 'info',
          'bg-gray-400': variant === 'neutral',
          'bg-brand-500': variant === 'brand',
        })} />
      )}
      {children}
    </span>
  );
}
