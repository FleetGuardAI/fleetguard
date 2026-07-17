import { cn } from '@/utils/cn';

export function Card({ children, className, hover = false, padding = 'md' }) {
  const paddings = { none: '', sm: 'p-4', md: 'p-6', lg: 'p-8' };
  return (
    <div className={cn(
      'bg-surface border border-border rounded-xl shadow-card transition-all duration-200',
      hover && 'hover:shadow-elevated hover:-translate-y-0.5 cursor-pointer',
      paddings[padding],
      className
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }) {
  return <div className={cn('mb-4', className)}>{children}</div>;
}

export function CardTitle({ children, className }) {
  return <h3 className={cn('text-lg font-semibold text-content', className)}>{children}</h3>;
}

export function CardDescription({ children, className }) {
  return <p className={cn('text-sm text-content-secondary mt-1', className)}>{children}</p>;
}
