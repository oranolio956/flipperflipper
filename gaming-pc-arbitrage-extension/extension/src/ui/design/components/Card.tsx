import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
}

export function Card({ 
  className, 
  variant = 'default', 
  padding = 'md',
  interactive = false,
  children,
  ...props 
}: CardProps) {
  return (
    <div
      className={cn(
        'card',
        `card-${variant}`,
        padding !== 'none' && `card-padding-${padding}`,
        interactive && 'card-interactive',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export function CardHeader({ 
  className, 
  title, 
  description, 
  action,
  children,
  ...props 
}: CardHeaderProps) {
  return (
    <div className={cn('card-header', className)} {...props}>
      <div className="card-header-content">
        {title && <h3 className="card-title">{title}</h3>}
        {description && <p className="card-description">{description}</p>}
        {children}
      </div>
      {action && <div className="card-header-action">{action}</div>}
    </div>
  );
}

export function CardContent({ 
  className, 
  children, 
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('card-content', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ 
  className, 
  children, 
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('card-footer', className)} {...props}>
      {children}
    </div>
  );
}

// CSS for Card component
export const cardStyles = `
.card {
  background-color: var(--card-bg);
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--easing-default);
}

/* Variants */
.card-default {
  border: var(--border-width) solid var(--card-border);
}

.card-bordered {
  border: var(--border-width) solid var(--border-secondary);
}

.card-elevated {
  box-shadow: var(--card-shadow);
  border: none;
}

/* Padding */
.card-padding-sm {
  padding: var(--space-3);
}

.card-padding-md {
  padding: var(--space-4);
}

.card-padding-lg {
  padding: var(--space-6);
}

/* Interactive */
.card-interactive {
  cursor: pointer;
}

.card-interactive:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.card-interactive:active {
  transform: translateY(0);
}

/* Card sections */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border-bottom: var(--border-width) solid var(--border-primary);
}

.card-header + .card-content {
  padding-top: var(--space-4);
}

.card-header-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
  margin: 0;
}

.card-description {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
  margin: var(--space-1) 0 0;
}

.card-header-action {
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: var(--border-width) solid var(--border-primary);
}

/* Remove padding when using sections */
.card-header:first-child,
.card-content:first-child,
.card-footer:first-child {
  padding-top: var(--space-4);
}

.card-header:last-child,
.card-content:last-child,
.card-footer:last-child {
  padding-bottom: var(--space-4);
}

.card-padding-none > .card-header,
.card-padding-none > .card-content,
.card-padding-none > .card-footer {
  padding-left: 0;
  padding-right: 0;
}
`;