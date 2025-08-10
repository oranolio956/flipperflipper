# 3. UX/UI Design Specification

## 3.1 Design Philosophy

The ProxyAssessmentTool follows Microsoft's Fluent Design System principles:
- **Light**: Illumination and shadows for depth
- **Depth**: Layering and elevation for hierarchy
- **Motion**: Smooth transitions and animations
- **Material**: Acrylic and transparency effects
- **Scale**: Responsive design across screen sizes

## 3.2 Visual Design

### 3.2.1 Color Palette

**Light Theme**
- Primary: #0078D4 (Windows Blue)
- Secondary: #00BCF2 (Light Blue)
- Success: #107C10 (Green)
- Warning: #FF8C00 (Orange)
- Error: #E81123 (Red)
- Background: #FFFFFF
- Surface: #F3F3F3
- Text Primary: #000000
- Text Secondary: #666666

**Dark Theme**
- Primary: #0099FF
- Secondary: #00D1FF
- Success: #16C60C
- Warning: #FFA500
- Error: #FF4444
- Background: #202020
- Surface: #2D2D2D
- Text Primary: #FFFFFF
- Text Secondary: #B3B3B3

### 3.2.2 Typography

- **Headlines**: Segoe UI Variable Display, 28px, SemiBold
- **Subheadlines**: Segoe UI Variable Display, 20px, Regular
- **Body**: Segoe UI Variable Text, 14px, Regular
- **Caption**: Segoe UI Variable Text, 12px, Regular
- **Monospace**: Cascadia Code, 13px (for IPs, codes)

### 3.2.3 Iconography

Using Fluent UI System Icons:
- Dashboard: GridDashboard
- Discovery: NetworkInspection
- Validation: ShieldCheckmark
- Findings: SearchInfo
- Reports: DocumentBulletList
- Settings: Settings
- Help: QuestionCircle

## 3.3 Layout Structure

### 3.3.1 Main Window

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Logo] ProxyAssessmentTool          [User] [Theme] [?]  │ │ Title Bar
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────┬─────────────────────────────────────────────┐   │
│ │         │                                             │   │
│ │  Nav    │              Content Area                   │   │
│ │  Panel  │                                             │   │
│ │         │                                             │   │
│ │ [Menu]  │                                             │   │
│ │ [Items] │                                             │   │
│ │         │                                             │   │
│ └─────────┴─────────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Status: Ready | Consent: ABC-123 | Last Scan: 2m ago   │ │ Status Bar
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.3.2 Navigation Panel

```xaml
<NavigationView>
    <NavigationViewItem Icon="GridDashboard" Content="Dashboard" Tag="dashboard"/>
    <NavigationViewItem Icon="ShieldKeyhole" Content="Scope & Consent" Tag="consent"/>
    <NavigationViewItem Icon="NetworkInspection" Content="Discovery" Tag="discovery"/>
    <NavigationViewItem Icon="ShieldCheckmark" Content="Validation" Tag="validation"/>
    <NavigationViewItem Icon="SearchInfo" Content="Findings" Tag="findings"/>
    <NavigationViewItem Icon="DocumentBulletList" Content="Reports" Tag="reports"/>
    <NavigationViewItemSeparator/>
    <NavigationViewItem Icon="Settings" Content="Settings" Tag="settings"/>
</NavigationView>
```

## 3.4 Screen Specifications

### 3.4.1 Dashboard View

**Purpose**: Overview of system status and key metrics

**Components**:
1. **Summary Cards** (Grid Layout)
   - Total Proxies Found
   - Eligible Proxies (SOCKS5, no-auth, fraud=0, US mobile)
   - Remediation Required
   - Last Scan Time

2. **Risk Distribution** (Doughnut Chart)
   - Critical: Red
   - High: Orange
   - Medium: Yellow
   - Low: Green

3. **Geographic Distribution** (US Map)
   - Heat map by state
   - Click for state details

4. **Recent Activity** (Timeline)
   - Last 10 operations
   - Live updates

5. **Quick Actions**
   - Start New Scan
   - View Latest Report
   - Check Uptime

**Empty State**: "No scans performed yet. Start your first scan to see metrics."

### 3.4.2 Scope & Consent View

**Purpose**: Manage authorization and scanning scope

**Components**:
1. **Consent Management**
   ```
   ┌─────────────────────────────────────┐
   │ Active Consent                      │
   │ ID: ABC-123                         │
   │ Expires: 2024-12-31                 │
   │ [View Details] [Renew] [Revoke]     │
   └─────────────────────────────────────┘
   ```

2. **Authorized Networks** (DataGrid)
   - CIDR blocks
   - Cloud accounts
   - Named environments
   - Actions: Add, Edit, Remove

3. **Do-Not-Scan List** (ListBox)
   - Excluded IPs/ranges
   - Import/Export functionality

4. **Consent History** (Timeline)
   - Audit trail of changes

**Validation**:
- Valid CIDR notation
- No overlapping ranges
- Consent ID required

### 3.4.3 Discovery View

**Purpose**: Configure and execute network discovery

**Components**:
1. **Scan Configuration**
   - Target Selection (from authorized)
   - Port Ranges (default: proxy ports)
   - Rate Limiting (requests/min)
   - Scan Window (time restrictions)

2. **Progress Visualization**
   ```
   ┌─────────────────────────────────────┐
   │ Scanning Progress                   │
   │ ████████████░░░░░░░░  60%          │
   │ Networks: 3/5 | Hosts: 1,234/2,048  │
   │ [Pause] [Stop] [Emergency Stop]     │
   └─────────────────────────────────────┘
   ```

3. **Live Results** (Virtual DataGrid)
   - IP Address
   - Port
   - Protocol (detected)
   - Status
   - Response Time

4. **Scan Log** (TextBox)
   - Real-time logging
   - Filterable by severity

**States**:
- Idle
- Configuring
- Running (with pause/resume)
- Completed
- Error

### 3.4.4 Validation View

**Purpose**: Show proxy validation results

**Components**:
1. **Validation Queue**
   - Pending validations
   - In-progress with ETA
   - Completed count

2. **Results Grid**
   - Proxy endpoint
   - Protocol version
   - Auth methods
   - Canary test result
   - Eligibility status

3. **Detail Panel** (Master-Detail)
   - Full handshake transcript
   - Auth negotiation details
   - Error messages
   - Retry options

4. **Filters**
   - By protocol
   - By auth method
   - By status
   - By eligibility

### 3.4.5 Findings View

**Purpose**: Comprehensive proxy listing with all enrichment data

**Components**:
1. **Advanced Filter Bar**
   ```
   Protocol: [SOCKS5 ▼] Auth: [No-Auth ▼] Fraud: [0 ▼]
   Country: [US ▼] Mobile: [Yes ▼] Usage: [Any ▼]
   [Apply] [Reset] [Save Filter]
   ```

2. **Results Grid** (Virtualized)
   | IP:Port | Protocol | Auth | Fraud | Location | ASN | Mobile | Usage | Risk | Actions |
   |---------|----------|------|-------|----------|-----|--------|-------|------|---------|

3. **Bulk Actions**
   - Export Selected
   - Generate Report
   - Create Tickets
   - Tag/Categorize

4. **Detail View** (Expandable Row)
   - Complete proxy information
   - Evidence links
   - Remediation suggestions
   - History graph

**Sorting**: All columns sortable
**Grouping**: By any column
**Export**: CSV, JSON, Excel

### 3.4.6 Reports View

**Purpose**: Generate and manage assessment reports

**Components**:
1. **Report Templates**
   - Executive Summary
   - Technical Details
   - Compliance Report
   - Remediation Plan

2. **Report Builder**
   ```
   ┌─────────────────────────────────────┐
   │ New Report                          │
   │ Template: [Executive Summary ▼]     │
   │ Date Range: [Last 30 days ▼]       │
   │ Include: ☑ Eligible ☑ Remediation  │
   │ Format: ◉ PDF ○ Word ○ HTML        │
   │ [Preview] [Generate]                │
   └─────────────────────────────────────┘
   ```

3. **Report History** (DataGrid)
   - Generated reports
   - Download links
   - Email status

4. **Distribution**
   - Email lists
   - Webhook configuration
   - Auto-generation schedule

### 3.4.7 Settings View

**Purpose**: Application configuration

**Tabs**:
1. **General**
   - Theme selection
   - Language (future)
   - Auto-update settings
   - Default paths

2. **Scanning**
   - Default port lists
   - Rate limit defaults
   - Timeout values
   - Retry policies

3. **Security**
   - Authentication method
   - Role assignments
   - SSO configuration
   - Audit settings

4. **Integrations**
   - SIEM configuration
   - Ticketing system
   - Webhook endpoints
   - API settings

5. **Advanced**
   - Database maintenance
   - Log retention
   - Performance tuning
   - Debug options

## 3.5 Interaction Patterns

### 3.5.1 Data Entry
- **Validation**: Real-time with helpful error messages
- **Auto-complete**: For common values (ports, CIDRs)
- **Tooltips**: Context-sensitive help
- **Undo/Redo**: For critical operations

### 3.5.2 Feedback
- **Progress**: Clear indicators for long operations
- **Notifications**: Toast for important events
- **Confirmations**: Modal dialogs for destructive actions
- **Success/Error**: Clear visual feedback

### 3.5.3 Navigation
- **Keyboard**: Full keyboard navigation support
- **Breadcrumbs**: For deep navigation
- **Back/Forward**: Browser-like navigation
- **Search**: Global search with filters

## 3.6 Accessibility

### 3.6.1 WCAG 2.2 AA Compliance
- **Color Contrast**: 4.5:1 for normal text, 3:1 for large
- **Focus Indicators**: Visible keyboard focus
- **Screen Reader**: Full NVDA/JAWS support
- **Keyboard**: All functionality keyboard accessible

### 3.6.2 High Contrast Mode
- Automatic detection
- Custom high contrast theme
- Preserved functionality

### 3.6.3 Accommodations
- **Font Scaling**: 100% to 200%
- **Motion Reduction**: Respect system preference
- **Audio Cues**: Optional for events
- **Tooltips**: Delayed on hover

## 3.7 Empty States & Error Handling

### 3.7.1 Empty States
Each view has helpful empty states:
- Illustration or icon
- Clear explanation
- Action button to get started

### 3.7.2 Error States
- **Inline Errors**: For form validation
- **Error Boundaries**: Graceful component failures
- **Retry Options**: For recoverable errors
- **Support Links**: For persistent issues

## 3.8 Onboarding Flow

### 3.8.1 First Run Wizard
1. **Welcome**
   - App overview
   - Safety reminder

2. **Consent Setup**
   - Enter consent ID
   - Define initial scope
   - Set do-not-scan list

3. **Configuration**
   - Choose theme
   - Set up integrations
   - Configure notifications

4. **Tutorial**
   - Interactive walkthrough
   - Sample data option
   - Help resources

### 3.8.2 Contextual Help
- **Coach marks**: For new features
- **Tooltips**: On hover/focus
- **Help panel**: F1 context-sensitive
- **Video tutorials**: Linked from help

## 3.9 Performance Considerations

### 3.9.1 Virtualization
- DataGrids use UI virtualization
- Lazy loading for large datasets
- Pagination options available

### 3.9.2 Responsiveness
- Async operations don't block UI
- Progress indication for >0.5s operations
- Cancelable long-running tasks

### 3.9.3 Caching
- Recent filters cached
- Common queries optimized
- Images/icons bundled

## 3.10 Gotchas & Pitfalls

### 3.10.1 UX Pitfalls
1. **Information Overload**
   - Solution: Progressive disclosure, collapsible sections

2. **Complex Filters**
   - Solution: Saved filter sets, smart defaults

3. **Long Lists**
   - Solution: Virtualization, search, pagination

4. **Modal Proliferation**
   - Solution: Inline editing where possible

### 3.10.2 Technical Gotchas
1. **DPI Scaling**
   - Solution: Vector graphics, DPI-aware layouts

2. **Theme Switching**
   - Solution: Dynamic resource binding

3. **Memory Leaks**
   - Solution: Proper event unsubscription

4. **Slow Databinding**
   - Solution: Async loading, virtualization

## 3.11 Quality Checks

### 3.11.1 Design Review
- Consistency with Fluent Design
- Accessibility compliance
- Performance benchmarks
- Usability testing results

### 3.11.2 Implementation Review
- XAML best practices
- MVVM pattern adherence
- Resource optimization
- Memory profiling