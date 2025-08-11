import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  duration?: number;
}

// Global toast state (in production, use a state management solution)
let toastListeners: ((toasts: ToastMessage[]) => void)[] = [];
let toastMessages: ToastMessage[] = [];

export function showToast(toast: Omit<ToastMessage, 'id'>) {
  const id = Date.now().toString();
  const newToast = { ...toast, id };
  toastMessages = [...toastMessages, newToast];
  toastListeners.forEach(listener => listener(toastMessages));

  // Auto dismiss
  if (toast.duration !== 0) {
    setTimeout(() => {
      dismissToast(id);
    }, toast.duration || 5000);
  }
}

export function dismissToast(id: string) {
  toastMessages = toastMessages.filter(t => t.id !== id);
  toastListeners.forEach(listener => listener(toastMessages));
}

export function Toast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const listener = (newToasts: ToastMessage[]) => setToasts(newToasts);
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter(l => l !== listener);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" role="region" aria-live="polite" aria-label="Notifications">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn('toast', `toast-${toast.type}`)}
          role="alert"
        >
          <div className="toast-icon">
            {toast.type === 'success' && <CheckCircle size={20} />}
            {toast.type === 'error' && <AlertCircle size={20} />}
            {toast.type === 'warning' && <AlertTriangle size={20} />}
            {toast.type === 'info' && <Info size={20} />}
          </div>
          <div className="toast-content">
            <h4 className="toast-title">{toast.title}</h4>
            {toast.description && (
              <p className="toast-description">{toast.description}</p>
            )}
          </div>
          <button
            className="toast-close"
            onClick={() => dismissToast(toast.id)}
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

// CSS for Toast component
export const toastStyles = `
.toast-container {
  position: fixed;
  bottom: var(--space-4);
  right: var(--space-4);
  z-index: var(--z-tooltip);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 24rem;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background-color: var(--bg-secondary);
  border: var(--border-width) solid var(--border-secondary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  pointer-events: auto;
  animation: slideInRight var(--duration-base) var(--easing-out);
}

.toast-icon {
  flex-shrink: 0;
  width: 1.25rem;
  height: 1.25rem;
}

.toast-success .toast-icon {
  color: var(--color-success);
}

.toast-error .toast-icon {
  color: var(--color-error);
}

.toast-warning .toast-icon {
  color: var(--color-warning);
}

.toast-info .toast-icon {
  color: var(--color-info);
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
  margin: 0;
}

.toast-description {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
  margin: var(--space-1) 0 0;
}

.toast-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-default);
}

.toast-close:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.toast-close:focus-visible {
  outline: var(--focus-ring-width) solid var(--border-focus);
  outline-offset: 0;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 640px) {
  .toast-container {
    left: var(--space-4);
    right: var(--space-4);
    max-width: none;
  }
}
`;