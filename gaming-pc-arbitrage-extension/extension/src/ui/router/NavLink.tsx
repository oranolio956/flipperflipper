import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import * as Icons from 'lucide-react';
import { ROUTE_META } from './routes';

interface NavLinkProps {
  to: string;
  children?: React.ReactNode;
  className?: string;
  activeClassName?: string;
  exactMatch?: boolean;
  showIcon?: boolean;
  showDescription?: boolean;
  onClick?: () => void;
}

export function NavLink({
  to,
  children,
  className,
  activeClassName = 'nav-link-active',
  exactMatch = false,
  showIcon = false,
  showDescription = false,
  onClick,
}: NavLinkProps) {
  const location = useLocation();
  const isActive = exactMatch 
    ? location.pathname === to
    : location.pathname.startsWith(to) && to !== '/';

  const meta = ROUTE_META[to as keyof typeof ROUTE_META];
  const Icon = meta?.icon ? Icons[meta.icon as keyof typeof Icons] : null;

  return (
    <Link
      to={to}
      className={cn(
        'nav-link',
        className,
        isActive && activeClassName
      )}
      aria-current={isActive ? 'page' : undefined}
      onClick={onClick}
    >
      <span className="nav-link-content">
        {showIcon && Icon && (
          <Icon className="nav-link-icon" aria-hidden="true" />
        )}
        <span className="nav-link-label">
          {children || meta?.title}
        </span>
        {showDescription && meta?.description && (
          <span className="nav-link-description">
            {meta.description}
          </span>
        )}
      </span>
    </Link>
  );
}

// Breadcrumb component using the route metadata
export function Breadcrumbs() {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);
  
  const breadcrumbs = pathSegments.map((segment, index) => {
    const path = '/' + pathSegments.slice(0, index + 1).join('/');
    const meta = ROUTE_META[path as keyof typeof ROUTE_META];
    
    return {
      path,
      label: meta?.title || segment,
      isLast: index === pathSegments.length - 1,
    };
  });

  if (breadcrumbs.length === 0) {
    breadcrumbs.push({
      path: '/',
      label: 'Home',
      isLast: true,
    });
  }

  return (
    <nav aria-label="Breadcrumb" className="breadcrumbs">
      <ol className="breadcrumb-list">
        {breadcrumbs.map((crumb, index) => (
          <li key={crumb.path} className="breadcrumb-item">
            {crumb.isLast ? (
              <span aria-current="page">{crumb.label}</span>
            ) : (
              <>
                <Link to={crumb.path}>{crumb.label}</Link>
                <span aria-hidden="true" className="breadcrumb-separator">
                  /
                </span>
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}