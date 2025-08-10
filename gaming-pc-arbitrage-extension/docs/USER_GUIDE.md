# User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Features](#core-features)
3. [Advanced Features](#advanced-features)
4. [Workflow Guide](#workflow-guide)
5. [Tips & Tricks](#tips--tricks)
6. [FAQ](#faq)

## Getting Started

### First-Time Setup

1. **Install the Extension**
   - Download from Chrome Web Store or load unpacked
   - Grant necessary permissions when prompted

2. **Initial Configuration**
   - Open extension popup
   - Click "Settings"
   - Configure:
     - Location (zip code, max distance)
     - Target ROI (recommended: 25%+)
     - Minimum deal value
     - Notification preferences

3. **Connect Platforms**
   - Visit Facebook Marketplace
   - Extension will activate automatically
   - Repeat for Craigslist and OfferUp

### Understanding the Interface

#### Popup Menu
- **Quick Stats**: Today's metrics at a glance
- **Active Deals**: Current pipeline count
- **Quick Actions**: Common tasks

#### Dashboard
- **Pipeline View**: Visual deal flow
- **Inventory**: Stock management
- **Analytics**: Performance metrics
- **P&L**: Financial tracking

## Core Features

### 1. Listing Analysis

When viewing a gaming PC listing, the extension provides:

**Instant Overlay**
- Fair Market Value (FMV)
- ROI percentage
- Risk score
- Quick action buttons

**Color Coding**
- 🟢 Green: Excellent deal (ROI > 25%)
- 🟡 Yellow: Good deal (ROI 15-25%)
- 🟠 Orange: Marginal deal (ROI 10-15%)
- 🔴 Red: Poor deal or high risk

### 2. Component Detection

The extension automatically detects:
- CPU model and generation
- GPU model and VRAM
- RAM capacity and speed
- Storage type and size
- Power supply wattage
- Case and cooling

**Manual Override**
If detection fails:
1. Click "Edit Specs"
2. Correct any errors
3. Save for accurate valuation

### 3. Deal Tracking

**Adding Deals**
1. Click "Track Deal" on any listing
2. Automatic:
   - Saves listing details
   - Calculates metrics
   - Sets initial stage
3. Optional:
   - Add notes
   - Set reminders
   - Tag for categories

**Deal Stages**
- Discovered → Evaluating → Negotiating → Scheduled → Acquired → Testing → Listing → Sold → Completed

### 4. Messaging Templates

**Using Templates**
1. Click message icon on listing
2. Select template category:
   - Initial inquiry
   - Negotiation
   - Scheduling
   - Follow-up
3. Customize variables
4. Copy to clipboard
5. Paste in platform messenger

**Creating Custom Templates**
1. Dashboard → Settings → Templates
2. Click "New Template"
3. Use variables: {{price}}, {{item}}, {{location}}
4. Save with descriptive name

## Advanced Features

### 1. Market Intelligence

**Comp Analysis**
- View similar sold listings
- Price trend graphs
- Seasonal adjustments
- Regional pricing

**Competitor Tracking**
- Monitor other sellers
- Price positioning
- Inventory overlap
- Response time analysis

### 2. Automation Features

**Price Drop Monitoring**
- Set target prices
- Get instant alerts
- Auto-calculate new ROI
- One-click re-evaluation

**Bulk Operations**
- Import multiple listings
- Batch analysis
- Export to spreadsheet
- Bulk messaging prep

### 3. Route Optimization

**Planning Pickups**
1. Select multiple deals
2. Click "Optimize Route"
3. Review suggested order
4. Export to Google Maps
5. Track time/distance

### 4. Financial Tools

**P&L Tracking**
- Automatic calculation
- Category breakdown
- Tax report export
- Expense tracking

**ROI Optimization**
- What-if scenarios
- Bundle suggestions
- Pricing strategies
- Market timing

## Workflow Guide

### Complete Deal Flow

#### 1. Discovery Phase
```
Browse Marketplace → Extension analyzes → Green overlay appears
↓
Click "Track Deal" → Added to pipeline → Stage: Discovered
```

#### 2. Evaluation Phase
```
Review comps → Check seller profile → Assess condition
↓
Run risk analysis → Verify specs → Stage: Evaluating
```

#### 3. Negotiation Phase
```
Select template → Customize message → Send to seller
↓
Track responses → Counter offers → Stage: Negotiating
```

#### 4. Acquisition Phase
```
Schedule pickup → Optimize route → Meet seller
↓
Test components → Complete purchase → Stage: Acquired
```

#### 5. Resale Phase
```
Clean/upgrade → Take photos → Create listing
↓
Price competitively → Track views → Stage: Listing
```

#### 6. Completion Phase
```
Negotiate with buyer → Schedule sale → Complete transaction
↓
Update records → Calculate profit → Stage: Completed
```

### Quick Flip Strategy

For same-day turnaround:

1. **Morning**
   - Check overnight listings
   - Message top 5 prospects
   - Schedule pickups

2. **Afternoon**
   - Complete pickups
   - Quick testing
   - Create listings

3. **Evening**
   - Respond to inquiries
   - Schedule next-day sales
   - Update pipeline

## Tips & Tricks

### Maximizing ROI

1. **Focus on Complete Systems**
   - Higher margins than parts
   - Easier to flip
   - Less technical knowledge needed

2. **Target Specific Brands**
   - Alienware: +10-15% premium
   - ASUS ROG: Strong demand
   - Custom builds: Verify quality

3. **Optimal Timing**
   - List Thursday evening
   - Best prices: Friday-Sunday
   - Avoid Monday-Tuesday

### Risk Mitigation

1. **Red Flags to Avoid**
   - "Urgent sale" with no reason
   - Prices 50%+ below market
   - No photos of internals
   - Refuses to power on

2. **Safe Transaction Tips**
   - Meet at police stations
   - Bring outlet tester
   - Test all components
   - Get receipts

### Efficiency Hacks

1. **Keyboard Shortcuts**
   - `Alt+A`: Analyze listing
   - `Alt+T`: Track deal
   - `Alt+D`: Dashboard
   - `Alt+M`: Messages

2. **Quick Filters**
   - High ROI only
   - New listings (< 1 hour)
   - Within 10 miles
   - RTX 30-series

3. **Batch Processing**
   - Morning: Review all new
   - Afternoon: Send messages
   - Evening: Update pipeline

## FAQ

### General Questions

**Q: Is this extension free?**
A: The basic version is free. Pro features available with subscription.

**Q: Which platforms are supported?**
A: Facebook Marketplace, Craigslist, and OfferUp currently.

**Q: Does it work on mobile?**
A: Extension is desktop Chrome only. Mobile companion app planned.

### Technical Questions

**Q: How accurate is the pricing?**
A: 85-90% accurate based on recent sold data and ML models.

**Q: Can I export my data?**
A: Yes, via Dashboard → Settings → Export Data.

**Q: Is my data private?**
A: All data stored locally. No cloud sync unless explicitly enabled.

### Troubleshooting

**Q: Extension not detecting listings?**
A: Try:
1. Refresh the page
2. Check extension is enabled
3. Clear cache
4. Report issue with URL

**Q: Prices seem wrong?**
A: Check:
1. Location settings
2. Component detection
3. Update price database
4. Manual override if needed

**Q: Performance issues?**
A: Try:
1. Reduce tracked deals to < 50
2. Clear old completed deals
3. Disable unused features
4. Check Chrome memory usage

---

For more help, visit our [Support Forum](https://github.com/yourusername/gaming-pc-arbitrage/discussions) or check the [Video Tutorials](https://youtube.com/playlist).