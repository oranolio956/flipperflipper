import React from 'react';
import { NavLink as RouterNavLink, NavLinkProps } from 'react-router-dom';
import { cn } from '@/lib/utils';

/**
 * Enhanced NavLink with Apple-grade active states
 * Handles focus management and accessibility
 */
export const NavLink = React.forwardRef<
  HTMLAnchorElement,
  NavLinkProps & { icon?: React.ReactNode }
>(({ className, children, icon, ...props }, ref) => {
  return (
    <RouterNavLink
      ref={ref}
      className={({ isActive, isPending }) =>
        cn(
          // Base styles
          'group relative flex items-center gap-3 rounded-lg px-3 py-2',
          'text-sm font-medium transition-all duration-150',
          'hover:bg-gray-100 dark:hover:bg-gray-800',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
          
          // Active state
          isActive && [
            'bg-indigo-50 text-indigo-700',
            'dark:bg-indigo-900/20 dark:text-indigo-400',
            'before:absolute before:inset-y-2 before:left-0 before:w-0.5',
            'before:bg-indigo-600 before:rounded-full',
            'dark:before:bg-indigo-400'
          ],
          
          // Pending state
          isPending && 'opacity-60',
          
          // Custom className
          className
        )
      }
      aria-current={props['aria-current'] || 'page'}
      {...props}
    >
      {icon && (
        <span className="flex-shrink-0 text-gray-500 group-hover:text-gray-700 dark:text-gray-400 dark:group-hover:text-gray-200">
          {icon}
        </span>
      )}
      {children}
    </RouterNavLink>
  );
});

NavLink.displayName = 'NavLink';

// Breadcrumb variant
export const BreadcrumbLink = React.forwardRef<
  HTMLAnchorElement,
  NavLinkProps
>(({ className, ...props }, ref) => {
  return (
    <RouterNavLink
      ref={ref}
      className={({ isActive }) =>
        cn(
          'text-sm transition-colors duration-150',
          isActive
            ? 'text-gray-900 dark:text-gray-100 font-medium'
            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
          className
        )
      }
      {...props}
    />
  );
});

BreadcrumbLink.displayName = 'BreadcrumbLink';