import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { slugToTitle } from '@/utils/formatters';
import { cn } from '@/utils/cn';

export function Breadcrumbs({ className }) {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  const crumbs = segments.map((segment, i) => {
    const path = '/' + segments.slice(0, i + 1).join('/');
    const isLast = i === segments.length - 1;
    const isId = /^[a-z0-9]{2,}$/i.test(segment) && segment.length < 10 && !['new', 'edit'].includes(segment);
    const label = isId ? `#${segment}` : slugToTitle(segment);
    return { path, label, isLast };
  });
  
  return (
    <nav className={cn('flex items-center gap-1.5 text-sm', className)}>
      <Link to="/dashboard" className="text-content-muted hover:text-content transition-colors">
        <Home className="h-4 w-4" />
      </Link>
      {crumbs.map(crumb => (
        <div key={crumb.path} className="flex items-center gap-1.5">
          <ChevronRight className="h-3.5 w-3.5 text-content-muted" />
          {crumb.isLast ? (
            <span className="text-content font-medium">{crumb.label}</span>
          ) : (
            <Link to={crumb.path} className="text-content-muted hover:text-content transition-colors">
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
