import React, { forwardRef } from 'react';
import { NavLink as RouterNavLink, NavLinkProps } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface ExtendedNavLinkProps extends Omit<NavLinkProps, 'className'> {
  className?: string | ((props: { isActive: boolean; isPending: boolean }) => string);
  activeClassName?: string;
  pendingClassName?: string;
  icon?: React.ReactNode;
  badge?: string | number;
  description?: string;
  shortcut?: string;
  variant?: 'sidebar' | 'tabs' | 'inline';
}

/**
 * Apple-grade NavLink with accessibility and performance optimizations
 * - Supports active/pending states with smooth transitions
 * - Keyboard navigation with proper focus management
 * - Prefetching on hover for instant navigation
 * - ARIA attributes for screen readers
 */
export const NavLink = forwardRef<HTMLAnchorElement, ExtendedNavLinkProps>(
  (
    {
      children,
      className,
      activeClassName = '',
      pendingClassName = '',
      icon,
      badge,
      description,
      shortcut,
      variant = 'sidebar',
      prefetch = 'intent',
      ...props
    },
    ref
  ) => {
    const baseStyles = {
      sidebar: 'group flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-150 hover:bg-gray-100 dark:hover:bg-gray-800',
      tabs: 'relative px-4 py-2 text-sm font-medium transition-colors hover:text-foreground/80',
      inline: 'inline-flex items-center gap-1 text-sm transition-colors hover:text-foreground/80'
    };

    const activeStyles = {
      sidebar: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
      tabs: 'text-foreground border-b-2 border-blue-600',
      inline: 'text-blue-600 dark:text-blue-400'
    };

    const pendingStyles = {
      sidebar: 'opacity-60',
      tabs: 'opacity-60',
      inline: 'opacity-60'
    };

    return (
      <RouterNavLink
        ref={ref}
        className={({ isActive, isPending }) => {
          const base = baseStyles[variant];
          const active = isActive ? activeStyles[variant] : '';
          const pending = isPending ? pendingStyles[variant] : '';
          const custom = typeof className === 'function' 
            ? className({ isActive, isPending })
            : className;

          return cn(base, active, pending, activeClassName && isActive && activeClassName, pendingClassName && isPending && pendingClassName, custom);
        }}
        aria-current={({ isActive }) => isActive ? 'page' : undefined}
        {...props}
      >
        {({ isActive, isPending }) => (
          <>
            {icon && (
              <span className={cn(
                'flex-shrink-0 transition-transform duration-150',
                variant === 'sidebar' && 'w-5 h-5',
                variant === 'tabs' && 'w-4 h-4',
                variant === 'inline' && 'w-3 h-3',
                isActive && variant === 'sidebar' && 'scale-110'
              )}>
                {icon}
              </span>
            )}
            
            <span className="flex-1 flex flex-col">
              <span className={cn(
                'transition-colors duration-150',
                variant === 'sidebar' && 'text-sm font-medium',
                variant === 'tabs' && 'text-sm',
                variant === 'inline' && 'text-xs'
              )}>
                {children}
              </span>
              
              {description && variant === 'sidebar' && (
                <span className="text-xs text-muted-foreground mt-0.5">
                  {description}
                </span>
              )}
            </span>

            {badge !== undefined && (
              <span className={cn(
                'flex-shrink-0 transition-all duration-150',
                variant === 'sidebar' && 'ml-auto px-2 py-0.5 text-xs font-medium rounded-full',
                variant === 'tabs' && 'ml-2 px-1.5 py-0.5 text-xs rounded',
                isActive 
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
              )}>
                {badge}
              </span>
            )}

            {shortcut && variant === 'sidebar' && (
              <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-800 rounded">
                {shortcut}
              </kbd>
            )}

            {/* Loading indicator for pending state */}
            {isPending && (
              <span className="absolute inset-0 flex items-center justify-center">
                <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              </span>
            )}
          </>
        )}
      </RouterNavLink>
    );
  }
);

NavLink.displayName = 'NavLink';

// Compound components for complex navigation patterns
export const NavLinkGroup = ({ 
  children, 
  label 
}: { 
  children: React.ReactNode; 
  label: string;
}) => (
  <div className="space-y-1">
    <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
      {label}
    </h3>
    <nav className="space-y-1" role="navigation" aria-label={label}>
      {children}
    </nav>
  </div>
);

// Breadcrumb navigation with proper ARIA
export const Breadcrumbs = ({ 
  items 
}: { 
  items: Array<{ label: string; href?: string; current?: boolean }> 
}) => (
  <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-sm">
    {items.map((item, index) => (
      <React.Fragment key={index}>
        {index > 0 && (
          <span className="text-muted-foreground select-none">/</span>
        )}
        {item.href && !item.current ? (
          <NavLink to={item.href} variant="inline">
            {item.label}
          </NavLink>
        ) : (
          <span 
            className={cn(
              'text-foreground',
              item.current && 'font-medium'
            )}
            aria-current={item.current ? 'page' : undefined}
          >
            {item.label}
          </span>
        )}
      </React.Fragment>
    ))}
  </nav>
);