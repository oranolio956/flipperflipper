/**
 * Field Component - Reusable form field wrapper
 */

import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';

interface FieldProps {
  label: string;
  value: string | number | boolean;
  onChange: (value: string) => void;
  type?: 'text' | 'number' | 'email' | 'password' | 'switch' | 'textarea';
  placeholder?: string;
  helperText?: string;
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  disabled?: boolean;
}

export function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  helperText,
  min,
  max,
  step,
  required,
  disabled,
}: FieldProps) {
  const id = `field-${label.toLowerCase().replace(/\s+/g, '-')}`;

  const renderInput = () => {
    switch (type) {
      case 'switch':
        return (
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor={id}>{label}</Label>
              {helperText && (
                <p className="text-sm text-muted-foreground">{helperText}</p>
              )}
            </div>
            <Switch
              id={id}
              checked={value as boolean}
              onCheckedChange={(checked) => onChange(String(checked))}
              disabled={disabled}
            />
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-2">
            <Label htmlFor={id}>{label}</Label>
            <Textarea
              id={id}
              value={String(value)}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              disabled={disabled}
              rows={3}
            />
            {helperText && (
              <p className="text-sm text-muted-foreground">{helperText}</p>
            )}
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            <Label htmlFor={id}>{label}</Label>
            <Input
              id={id}
              type={type}
              value={String(value)}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              min={min}
              max={max}
              step={step}
              required={required}
              disabled={disabled}
            />
            {helperText && (
              <p className="text-sm text-muted-foreground">{helperText}</p>
            )}
          </div>
        );
    }
  };

  return <div className="w-full">{renderInput()}</div>;
}