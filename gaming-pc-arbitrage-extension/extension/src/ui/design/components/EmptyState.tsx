import React from 'react';
import { cn } from '../../lib/utils';
import { Button } from './Button';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  className
}: EmptyStateProps) {
  return (
    <div className={cn('empty-state', className)}>
      {Icon && (
        <div className="empty-state-icon">
          <Icon size={48} strokeWidth={1.5} />
        </div>
      )}
      
      <div className="empty-state-content">
        <h3 className="empty-state-title">{title}</h3>
        {description && (
          <p className="empty-state-description">{description}</p>
        )}
      </div>

      {(action || secondaryAction) && (
        <div className="empty-state-actions">
          {action && (
            <Button
              variant={action.variant || 'primary'}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant="ghost"
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// Loading state variant
interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({ 
  message = 'Loading...', 
  className 
}: LoadingStateProps) {
  return (
    <div className={cn('loading-state', className)}>
      <div className="loading-spinner" aria-label="Loading">
        <div className="spinner-ring"></div>
      </div>
      <p className="loading-message">{message}</p>
    </div>
  );
}

// Error state variant
interface ErrorStateProps {
  title?: string;
  message: string;
  retry?: () => void;
  className?: string;
}

export function ErrorState({ 
  title = 'Something went wrong', 
  message, 
  retry,
  className 
}: ErrorStateProps) {
  return (
    <div className={cn('error-state', className)}>
      <div className="error-state-content">
        <h3 className="error-state-title">{title}</h3>
        <p className="error-state-message">{message}</p>
      </div>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  );
}

// CSS for EmptyState components
export const emptyStateStyles = `
/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-12) var(--space-4);
  min-height: 24rem;
}

.empty-state-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 5rem;
  height: 5rem;
  margin-bottom: var(--space-4);
  color: var(--text-tertiary);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
}

.empty-state-content {
  max-width: 24rem;
  margin-bottom: var(--space-6);
}

.empty-state-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
  margin: 0 0 var(--space-2);
}

.empty-state-description {
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
  margin: 0;
}

.empty-state-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12) var(--space-4);
  min-height: 24rem;
}

.loading-spinner {
  position: relative;
  width: 3rem;
  height: 3rem;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border: 3px solid var(--border-primary);
  border-top-color: var(--accent-primary);
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

.loading-message {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  margin: 0;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--space-4);
  padding: var(--space-12) var(--space-4);
  min-height: 24rem;
  background-color: var(--color-error);
  background-color: color-mix(in srgb, var(--color-error) 5%, transparent);
  border-radius: var(--radius-lg);
}

.error-state-content {
  max-width: 24rem;
}

.error-state-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  color: var(--color-error);
  margin: 0 0 var(--space-2);
}

.error-state-message {
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--text-primary);
  margin: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
`;