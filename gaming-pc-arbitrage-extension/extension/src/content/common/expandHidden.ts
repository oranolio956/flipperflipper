/**
 * Expand Hidden Details
 * Reveal collapsed sections and hidden content
 */

export interface ExpandResult {
  sectionsExpanded: number;
  newContent: string[];
}

/**
 * Expand all collapsed sections
 */
export async function expandAllSections(): Promise<ExpandResult> {
  const result: ExpandResult = {
    sectionsExpanded: 0,
    newContent: [],
  };
  
  // Find expandable elements
  const expandables = findExpandableElements();
  
  for (const element of expandables) {
    const expanded = await expandElement(element);
    if (expanded) {
      result.sectionsExpanded++;
      
      // Capture new content
      const newText = extractNewContent(element);
      if (newText) {
        result.newContent.push(newText);
      }
    }
    
    // Small delay between expansions
    await delay(200);
  }
  
  return result;
}

/**
 * Find all expandable elements
 */
function findExpandableElements(): HTMLElement[] {
  const elements: HTMLElement[] = [];
  
  // Common patterns
  const selectors = [
    // Facebook
    '[role="button"]:has-text("See more")',
    'div[class*="seeMore"]',
    'span[dir="auto"]:has-text("...")',
    
    // Craigslist
    '.show-more',
    '.expand-button',
    
    // OfferUp
    '[data-testid="read-more"]',
    'button:has-text("Show more")',
    
    // Generic
    'button:contains("more")',
    'a:contains("expand")',
    '[aria-expanded="false"]',
    '[data-collapsed="true"]',
  ];
  
  // Try each selector
  for (const selector of selectors) {
    try {
      const found = document.querySelectorAll(selector);
      found.forEach(el => {
        if (el instanceof HTMLElement && !elements.includes(el)) {
          elements.push(el);
        }
      });
    } catch (e) {
      // Some selectors might not be valid
      continue;
    }
  }
  
  // Also find by text content
  const allButtons = document.querySelectorAll('button, [role="button"], a');
  allButtons.forEach(btn => {
    const text = btn.textContent?.toLowerCase() || '';
    if (
      (text.includes('see more') ||
       text.includes('show more') ||
       text.includes('read more') ||
       text.includes('expand') ||
       text === '...') &&
      btn instanceof HTMLElement &&
      !elements.includes(btn)
    ) {
      elements.push(btn);
    }
  });
  
  return elements;
}

/**
 * Expand a single element
 */
async function expandElement(element: HTMLElement): Promise<boolean> {
  try {
    // Store initial state
    const parentText = element.parentElement?.textContent || '';
    
    // Click the element
    element.click();
    
    // Wait for expansion
    await delay(300);
    
    // Check if content changed
    const newParentText = element.parentElement?.textContent || '';
    return newParentText.length > parentText.length;
  } catch (error) {
    console.error('Failed to expand element:', error);
    return false;
  }
}

/**
 * Extract new content after expansion
 */
function extractNewContent(element: HTMLElement): string | null {
  // Look for new text in parent
  const parent = element.parentElement;
  if (!parent) return null;
  
  // Get all text nodes
  const textContent = parent.textContent?.trim() || '';
  
  // Filter out button text
  const buttonText = element.textContent?.trim() || '';
  const cleanedContent = textContent.replace(buttonText, '').trim();
  
  // Only return if substantial content
  return cleanedContent.length > 50 ? cleanedContent : null;
}

/**
 * Create UI button for expansion
 */
export function createExpandButton(
  onExpand: () => void
): HTMLElement {
  const button = document.createElement('button');
  button.className = 'arbitrage-expand-button';
  button.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M3 12h18m-9-9v18"/>
    </svg>
    Expand Details
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .arbitrage-expand-button {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      color: #374151;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .arbitrage-expand-button:hover {
      background: #e5e7eb;
      border-color: #d1d5db;
    }
    
    .arbitrage-expand-button:active {
      transform: scale(0.95);
    }
    
    .arbitrage-expand-button svg {
      width: 16px;
      height: 16px;
    }
    
    .arbitrage-expand-button.expanding {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .arbitrage-expand-button.expanded {
      background: #dcfce7;
      border-color: #bbf7d0;
      color: #166534;
    }
    
    .arbitrage-expand-button.expanded svg {
      display: none;
    }
    
    .arbitrage-expand-button.expanded::before {
      content: "✓";
      margin-right: 4px;
    }
  `;
  
  document.head.appendChild(style);
  
  button.addEventListener('click', async () => {
    if (button.classList.contains('expanding')) return;
    
    button.classList.add('expanding');
    button.textContent = 'Expanding...';
    
    try {
      await onExpand();
      button.classList.remove('expanding');
      button.classList.add('expanded');
      button.textContent = 'Expanded';
    } catch (error) {
      button.classList.remove('expanding');
      button.textContent = 'Expand Failed';
      console.error('Expansion error:', error);
    }
  });
  
  return button;
}

/**
 * Auto-expand on page load
 */
export function autoExpandOnLoad(
  callback?: (result: ExpandResult) => void
): void {
  // Wait for page to settle
  setTimeout(async () => {
    const result = await expandAllSections();
    
    if (result.sectionsExpanded > 0) {
      console.log(`Expanded ${result.sectionsExpanded} sections`);
      callback?.(result);
    }
  }, 2000);
}

/**
 * Utility delay
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}