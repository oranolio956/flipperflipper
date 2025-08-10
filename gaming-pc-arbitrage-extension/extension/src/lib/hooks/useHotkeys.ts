/**
 * useHotkeys Hook
 * Keyboard shortcut management
 */

import { useEffect } from 'react';

interface Hotkey {
  key: string;
  handler: () => void | Promise<void>;
  preventDefault?: boolean;
}

/**
 * Parse hotkey string into components
 */
function parseHotkey(hotkey: string) {
  const parts = hotkey.toLowerCase().split('+');
  const key = parts[parts.length - 1];
  
  return {
    key,
    ctrl: parts.includes('ctrl'),
    cmd: parts.includes('cmd'),
    alt: parts.includes('alt'),
    shift: parts.includes('shift'),
  };
}

/**
 * Check if platform-specific modifier is pressed
 */
function checkModifier(e: KeyboardEvent, cmd: boolean, ctrl: boolean): boolean {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  
  if (isMac) {
    return cmd ? e.metaKey : !e.metaKey;
  } else {
    return ctrl ? e.ctrlKey : !e.ctrlKey;
  }
}

/**
 * Register keyboard shortcuts
 */
export function useHotkeys(hotkeys: Hotkey[]) {
  useEffect(() => {
    if (hotkeys.length === 0) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if typing in input
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }
      
      for (const hotkey of hotkeys) {
        const parsed = parseHotkey(hotkey.key);
        
        // Check key
        if (e.key.toLowerCase() !== parsed.key) continue;
        
        // Check modifiers
        if (!checkModifier(e, parsed.cmd, parsed.ctrl)) continue;
        if (parsed.alt && !e.altKey) continue;
        if (parsed.shift && !e.shiftKey) continue;
        
        // Match found
        if (hotkey.preventDefault !== false) {
          e.preventDefault();
          e.stopPropagation();
        }
        
        hotkey.handler();
        break;
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [hotkeys]);
}