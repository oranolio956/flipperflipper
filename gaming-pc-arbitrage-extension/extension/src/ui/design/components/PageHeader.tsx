import React, { useState } from 'react';
import { HelpCircle, X, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from './Button';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  helpContent?: React.ReactNode;
  breadcrumb?: Array<{ label: string; href?: string }>;
  className?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  helpContent,
  breadcrumb,
  className
}: PageHeaderProps) {
  const [showHelp, setShowHelp] = useState(false);

  return (
    <header className={cn('page-header', className)}>
      <div className="page-header-content">
        {breadcrumb && breadcrumb.length > 0 && (
          <nav aria-label="Breadcrumb" className="page-breadcrumb">
            {breadcrumb.map((item, index) => (
              <React.Fragment key={index}>
                {index > 0 && <ChevronRight size={16} className="breadcrumb-separator" />}
                {item.href ? (
                  <a href={item.href} className="breadcrumb-link">
                    {item.label}
                  </a>
                ) : (
                  <span className="breadcrumb-current">{item.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>
        )}
        
        <div className="page-header-main">
          <div className="page-header-text">
            <h1 className="page-title">
              {title}
              {helpContent && (
                <button
                  className="help-trigger"
                  onClick={() => setShowHelp(!showHelp)}
                  aria-label="Show help"
                  aria-expanded={showHelp}
                >
                  <HelpCircle size={20} />
                </button>
              )}
            </h1>
            {description && (
              <p className="page-description">{description}</p>
            )}
          </div>
          
          {actions && (
            <div className="page-header-actions">
              {actions}
            </div>
          )}
        </div>
      </div>

      {/* Help Popover */}
      {helpContent && showHelp && (
        <div className="help-popover" role="dialog" aria-label="Help information">
          <div className="help-popover-header">
            <h3 className="help-popover-title">How to use this page</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowHelp(false)}
              aria-label="Close help"
              icon={<X size={16} />}
            />
          </div>
          <div className="help-popover-content">
            {helpContent}
          </div>
        </div>
      )}
    </header>
  );
}

// CSS for PageHeader
export const pageHeaderStyles = `
.page-header {
  position: relative;
  margin-bottom: var(--space-6);
}

.page-header-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.page-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.breadcrumb-separator {
  color: var(--text-tertiary);
}

.breadcrumb-link {
  color: inherit;
  text-decoration: none;
  transition: color var(--duration-fast) var(--easing-default);
}

.breadcrumb-link:hover {
  color: var(--text-primary);
  text-decoration: underline;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.page-header-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.page-header-text {
  flex: 1;
  min-width: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
  margin: 0;
}

.help-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-default);
}

.help-trigger:hover {
  color: var(--text-secondary);
  background-color: var(--bg-tertiary);
}

.help-trigger:focus-visible {
  outline: var(--focus-ring-width) solid var(--border-focus);
  outline-offset: 0;
}

.page-description {
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
  margin: var(--space-1) 0 0;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

/* Help Popover */
.help-popover {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  z-index: var(--z-popover);
  width: 24rem;
  max-width: calc(100vw - var(--space-4));
  background-color: var(--bg-secondary);
  border: var(--border-width) solid var(--border-secondary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  animation: slideDown var(--duration-base) var(--easing-out);
}

.help-popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: var(--border-width) solid var(--border-primary);
}

.help-popover-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.help-popover-content {
  padding: var(--space-4);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  color: var(--text-secondary);
}

.help-popover-content h4 {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-1);
}

.help-popover-content ul {
  margin: var(--space-2) 0;
  padding-left: var(--space-4);
}

.help-popover-content li {
  margin: var(--space-1) 0;
}

.help-popover-content code {
  font-family: monospace;
  font-size: 0.875em;
  padding: 0.125em 0.25em;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-0.5rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .page-header-main {
    flex-direction: column;
  }
  
  .page-header-actions {
    width: 100%;
  }
  
  .help-popover {
    right: 0;
    left: 0;
    width: auto;
  }
}
`;