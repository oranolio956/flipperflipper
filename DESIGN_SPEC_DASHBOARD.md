# Modern Dashboard Design Specification

## Design Philosophy

Inspired by Stripe, Vercel, and Linear - clean, fast, intelligent information architecture.

---

## Key Principles

1. **Information Hierarchy**: Most critical data visible immediately
2. **Glanceable Metrics**: Key numbers without scrolling
3. **Progressive Disclosure**: Details on demand
4. **Real-time Updates**: Live data via WebSocket
5. **Responsive Design**: Desktop and mobile
6. **Performance**: Fast loading, smooth interactions
7. **Accessibility**: WCAG 2.1 AA compliant

---

## Color System (Modern Dark Theme)

```css
:root {
  /* Primary Colors */
  --primary: #6366f1;        /* Indigo - primary actions */
  --primary-hover: #4f46e5;
  --primary-light: #818cf8;
  
  /* Status Colors */
  --success: #10b981;        /* Green - online, success */
  --warning: #f59e0b;        /* Amber - warning, pending */
  --error: #ef4444;          /* Red - error, offline */
  --info: #3b82f6;           /* Blue - info */
  
  /* Background Colors */
  --bg-primary: #0f172a;     /* Slate 900 - main bg */
  --bg-secondary: #1e293b;   /* Slate 800 - cards */
  --bg-tertiary: #334155;    /* Slate 700 - hover */
  --bg-elevated: #475569;    /* Slate 600 - modals */
  
  /* Text Colors */
  --text-primary: #f1f5f9;   /* Slate 100 - headings */
  --text-secondary: #cbd5e1; /* Slate 300 - body */
  --text-tertiary: #94a3b8;  /* Slate 400 - muted */
  
  /* Border Colors */
  --border-primary: #334155;  /* Slate 700 */
  --border-secondary: #475569; /* Slate 600 */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
}
```

---

## Typography

```css
/* Font Stack */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Scale */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
```

---

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar (240px)  │  Main Content (flex-1)                  │
│                   │                                          │
│  Logo             │  Header Bar                              │
│  Navigation       │  ┌────────────────────────────────────┐ │
│  - Dashboard      │  │ Page Title    [Actions] [Profile]  │ │
│  - Connections    │  └────────────────────────────────────┘ │
│  - Commands       │                                          │
│  - Payloads       │  Content Area                            │
│  - Files          │  ┌────────────────────────────────────┐ │
│  - Logs           │  │                                    │ │
│                   │  │  Main content here                 │ │
│  Status           │  │                                    │ │
│  User Menu        │  │                                    │ │
└─────────────────────────────────────────────────────────────┘
```

---

## Dashboard Page Layout

### Above the Fold (No Scroll)

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                    [Profile ▾]    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ 🟢 12    │ ⚡ 1,234 │ ✓ 98.5%  │ ⚠️ 3     │             │
│  │ Active   │ Commands │ Success  │ Pending  │             │
│  │ Agents   │ Today    │ Rate     │ Commands │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
├─────────────────────────────────────────────────────────────┤
│  Active Connections                         [View All →]    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🟢 WORKSTATION-01  192.168.1.100  Windows 10  2m ago│   │
│  │ 🟢 SERVER-PROD     10.0.0.50      Ubuntu     5m ago │   │
│  │ 🟡 LAPTOP-MOBILE   172.16.0.10    macOS      15m ago│   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Stat Card
```html
<div class="stat-card">
  <div class="stat-icon">🟢</div>
  <div class="stat-value">12</div>
  <div class="stat-label">Active Agents</div>
  <div class="stat-change">+2 from yesterday</div>
</div>
```

### Connection Row
```html
<div class="connection-row">
  <div class="status-dot online"></div>
  <div class="hostname">WORKSTATION-01</div>
  <div class="ip">192.168.1.100</div>
  <div class="os">Windows 10</div>
  <div class="last-seen">2m ago</div>
  <div class="actions">
    <button>Execute</button>
    <button>Details</button>
  </div>
</div>
```

---

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 640px) {
  /* Stack cards vertically */
  /* Hide sidebar, show hamburger menu */
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  /* 2-column grid for cards */
  /* Collapsible sidebar */
}

/* Desktop */
@media (min-width: 1025px) {
  /* Full layout */
  /* Persistent sidebar */
}
```

---

## Interactions

### Hover States
- Cards: Subtle elevation increase
- Buttons: Background color change
- Rows: Background highlight

### Loading States
- Skeleton screens for initial load
- Spinners for actions
- Progress bars for uploads

### Empty States
- Friendly illustrations
- Clear call-to-action
- Helpful guidance

---

## Implementation Priority

1. ✅ Core layout and navigation
2. ✅ Dashboard overview page
3. ✅ Connections list and details
4. ✅ Command execution interface
5. ✅ Real-time updates
6. ⏳ Payload management
7. ⏳ File operations
8. ⏳ Advanced analytics

---

This specification provides a foundation for a modern, professional dashboard that users will trust and enjoy using.
