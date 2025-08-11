import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'primary', 
    size = 'md', 
    loading = false,
    fullWidth = false,
    icon,
    iconPosition = 'left',
    disabled,
    children,
    ...props 
  }, ref) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          'button',
          `button-${variant}`,
          `button-${size}`,
          fullWidth && 'button-full',
          loading && 'button-loading',
          className
        )}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <Loader2 className="button-spinner" aria-label="Loading" />
        )}
        {icon && iconPosition === 'left' && !loading && (
          <span className="button-icon button-icon-left">{icon}</span>
        )}
        {children && <span className="button-label">{children}</span>}
        {icon && iconPosition === 'right' && !loading && (
          <span className="button-icon button-icon-right">{icon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

// CSS for Button component (would be in a separate CSS file)
export const buttonStyles = `
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: var(--button-height);
  padding: 0 var(--button-padding-x);
  font-size: var(--button-font-size);
  font-weight: var(--button-font-weight);
  line-height: 1;
  border-radius: var(--radius-md);
  border: var(--border-width) solid transparent;
  transition: all var(--duration-base) var(--easing-default);
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.button:focus-visible {
  outline: var(--focus-ring-width) solid var(--border-focus);
  outline-offset: var(--focus-ring-offset);
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Variants */
.button-primary {
  background-color: var(--accent-primary);
  color: white;
}

.button-primary:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.button-primary:active:not(:disabled) {
  background-color: var(--accent-active);
}

.button-secondary {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--border-primary);
}

.button-secondary:hover:not(:disabled) {
  background-color: var(--bg-tertiary);
  border-color: var(--border-secondary);
}

.button-ghost {
  background-color: transparent;
  color: var(--text-secondary);
}

.button-ghost:hover:not(:disabled) {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.button-danger {
  background-color: var(--color-error);
  color: white;
}

.button-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

/* Sizes */
.button-sm {
  height: 2rem;
  padding: 0 var(--space-3);
  font-size: var(--font-size-xs);
}

.button-lg {
  height: 2.75rem;
  padding: 0 var(--space-6);
  font-size: var(--font-size-base);
}

/* States */
.button-full {
  width: 100%;
}

.button-loading {
  color: transparent;
}

.button-spinner {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 1em;
  height: 1em;
  animation: spin 1s linear infinite;
}

.button-icon {
  display: inline-flex;
  flex-shrink: 0;
}

.button-icon-left {
  margin-left: calc(var(--space-2) * -0.5);
}

.button-icon-right {
  margin-right: calc(var(--space-2) * -0.5);
}

@keyframes spin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}
`;