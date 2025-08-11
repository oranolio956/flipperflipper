import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  FileText, 
  Scan, 
  Plus, 
  Settings,
  HelpCircle,
  Zap,
  DollarSign,
  Package,
  Route,
  Users,
  FlaskConical
} from 'lucide-react';
import { ROUTES, ROUTE_META } from '../router/routes';
import { cn } from '../lib/utils';

interface Command {
  id: string;
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action: () => void;
  category: string;
  keywords?: string[];
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([]);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  // Build commands from routes and actions
  const commands: Command[] = [
    // Navigation commands
    ...Object.entries(ROUTE_META).map(([path, meta]) => ({
      id: `nav-${path}`,
      title: `Go to ${meta.title}`,
      description: meta.description,
      icon: getIconForRoute(meta.icon),
      action: () => {
        navigate(path);
        onClose();
      },
      category: 'Navigation',
      keywords: [meta.title.toLowerCase(), 'navigate', 'go']
    })),
    
    // Action commands
    {
      id: 'action-scan',
      title: 'Scan current page',
      description: 'Analyze the current marketplace page',
      icon: <Scan size={16} />,
      action: () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs[0]?.id) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'scan' });
          }
        });
        onClose();
      },
      category: 'Actions',
      keywords: ['scan', 'analyze', 'parse']
    },
    {
      id: 'action-new-deal',
      title: 'Create new deal',
      description: 'Add a deal to the pipeline',
      icon: <Plus size={16} />,
      action: () => {
        // Open new deal modal
        navigate(ROUTES.PIPELINE);
        onClose();
      },
      category: 'Actions',
      keywords: ['new', 'create', 'add', 'deal']
    },
    {
      id: 'action-toggle-automation',
      title: 'Toggle automation',
      description: 'Turn Max Auto on/off',
      icon: <Zap size={16} />,
      action: async () => {
        const { automationEnabled } = await chrome.storage.local.get(['automationEnabled']);
        await chrome.storage.local.set({ automationEnabled: !automationEnabled });
        onClose();
      },
      category: 'Actions',
      keywords: ['automation', 'auto', 'toggle', 'max']
    },
    {
      id: 'action-draft-message',
      title: 'Draft offer message',
      description: 'Generate an offer template',
      icon: <FileText size={16} />,
      action: () => {
        // Open message drafter
        navigate(ROUTES.PIPELINE);
        onClose();
      },
      category: 'Actions',
      keywords: ['draft', 'message', 'offer', 'template']
    }
  ];

  // Filter commands based on search
  useEffect(() => {
    if (!search) {
      setFilteredCommands(commands);
      setSelectedIndex(0);
      return;
    }

    const searchLower = search.toLowerCase();
    const filtered = commands.filter(cmd => {
      const titleMatch = cmd.title.toLowerCase().includes(searchLower);
      const descMatch = cmd.description?.toLowerCase().includes(searchLower);
      const keywordMatch = cmd.keywords?.some(k => k.includes(searchLower));
      return titleMatch || descMatch || keywordMatch;
    });

    setFilteredCommands(filtered);
    setSelectedIndex(0);
  }, [search]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(i => Math.max(i - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSearch('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div className="command-palette-backdrop" onClick={onClose} />
      <div className="command-palette" role="dialog" aria-modal="true" aria-label="Command palette">
        <div className="command-search">
          <Search size={20} className="search-icon" />
          <input
            ref={inputRef}
            type="text"
            className="command-input"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Command search"
          />
        </div>

        <div className="command-list" role="listbox">
          {filteredCommands.length === 0 ? (
            <div className="command-empty">
              No commands found for "{search}"
            </div>
          ) : (
            <>
              {groupCommandsByCategory(filteredCommands).map(([category, cmds]) => (
                <div key={category} className="command-group">
                  <div className="command-category">{category}</div>
                  {cmds.map((cmd, index) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        className={cn(
                          'command-item',
                          globalIndex === selectedIndex && 'selected'
                        )}
                        onClick={() => cmd.action()}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                        role="option"
                        aria-selected={globalIndex === selectedIndex}
                      >
                        {cmd.icon && <span className="command-icon">{cmd.icon}</span>}
                        <div className="command-content">
                          <div className="command-title">{cmd.title}</div>
                          {cmd.description && (
                            <div className="command-description">{cmd.description}</div>
                          )}
                        </div>
                        <kbd className="command-shortcut">↵</kbd>
                      </button>
                    );
                  })}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </>
  );
}

function getIconForRoute(iconName?: string): React.ReactNode {
  if (!iconName) return null;
  
  const icons: Record<string, React.ReactNode> = {
    LayoutDashboard: <DollarSign size={16} />,
    Scan: <Scan size={16} />,
    GitPullRequest: <Package size={16} />,
    FileText: <FileText size={16} />,
    DollarSign: <DollarSign size={16} />,
    Package: <Package size={16} />,
    Route: <Route size={16} />,
    Users: <Users size={16} />,
    Settings: <Settings size={16} />,
    Zap: <Zap size={16} />,
    HelpCircle: <HelpCircle size={16} />,
    FlaskConical: <FlaskConical size={16} />,
  };
  
  return icons[iconName] || null;
}

function groupCommandsByCategory(commands: Command[]): [string, Command[]][] {
  const groups = new Map<string, Command[]>();
  
  commands.forEach(cmd => {
    const group = groups.get(cmd.category) || [];
    group.push(cmd);
    groups.set(cmd.category, group);
  });
  
  return Array.from(groups.entries());
}

// CSS for CommandPalette
export const commandPaletteStyles = `
.command-palette-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgb(0 0 0 / 0.5);
  z-index: var(--z-modal-backdrop);
  animation: fadeIn var(--duration-fast) var(--easing-default);
}

.command-palette {
  position: fixed;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  width: 90vw;
  max-width: 40rem;
  max-height: 60vh;
  background-color: var(--bg-secondary);
  border: var(--border-width) solid var(--border-secondary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  z-index: var(--z-modal);
  display: flex;
  flex-direction: column;
  animation: slideDown var(--duration-base) var(--easing-out);
}

.command-search {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: var(--border-width) solid var(--border-primary);
}

.command-search .search-icon {
  color: var(--text-tertiary);
}

.command-input {
  flex: 1;
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
}

.command-input::placeholder {
  color: var(--text-tertiary);
}

.command-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.command-empty {
  padding: var(--space-8) var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
}

.command-group {
  margin-bottom: var(--space-2);
}

.command-category {
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  color: var(--text-tertiary);
}

.command-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-default);
}

.command-item:hover,
.command-item.selected {
  background-color: var(--bg-tertiary);
}

.command-item.selected {
  outline: var(--focus-ring-width) solid var(--border-focus);
  outline-offset: -2px;
}

.command-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  color: var(--text-tertiary);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.command-item.selected .command-icon {
  color: var(--accent-primary);
  background-color: color-mix(in srgb, var(--accent-primary) 10%, transparent);
}

.command-content {
  flex: 1;
  text-align: left;
}

.command-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
}

.command-description {
  font-size: var(--font-size-xs);
  line-height: var(--line-height-tight);
  color: var(--text-secondary);
  margin-top: var(--space-0-5);
}

.command-shortcut {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-tertiary);
  background-color: var(--bg-tertiary);
  border: var(--border-width) solid var(--border-primary);
  border-radius: var(--radius-sm);
  opacity: 0;
  transition: opacity var(--duration-fast) var(--easing-default);
}

.command-item.selected .command-shortcut {
  opacity: 1;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translate(-50%, -1rem);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}
`;