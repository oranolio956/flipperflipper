# Gaming PC Arbitrage Extension

A powerful Chrome extension for finding and flipping gaming PCs across Facebook Marketplace, Craigslist, and OfferUp. Built with privacy-first principles and ToS compliance.

## 🚀 Features

### Core Functionality
- **Real-time Listing Analysis**: Parse gaming PC specs from marketplace listings
- **Fair Market Value (FMV) Calculator**: Instant valuation based on components
- **ROI & Profit Calculations**: Know your margins before you buy
- **Deal Risk Assessment**: Avoid scams with pattern detection
- **Inventory Management**: Track your pipeline from acquisition to sale

### Advanced Features
- **ML Price Predictions**: AI-powered pricing recommendations
- **Market Comp Aggregation**: Historical sold data analysis
- **Competitor Tracking**: Monitor other flippers in your area
- **Bundle Optimization**: Maximize value with smart bundling
- **Route Planning**: Optimize pickup/delivery routes

### Automation (Human-in-the-Loop)
- **Message Templates**: Pre-written negotiation messages
- **Deal Flow Automation**: Automated stage transitions
- **Price Drop Alerts**: Real-time notifications
- **A/B Testing**: Optimize your listings
- **Bulk Operations**: Process multiple listings efficiently

## 📋 Requirements

- Chrome Browser (v100+)
- Node.js 18+ (for development)
- Active accounts on supported platforms

## 🛠️ Installation

### For Users
1. Download the latest release from [Releases](https://github.com/yourusername/gaming-pc-arbitrage/releases)
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right
4. Click "Load unpacked" and select the extracted folder
5. The extension icon will appear in your toolbar

### For Developers
```bash
# Clone the repository
git clone https://github.com/yourusername/gaming-pc-arbitrage.git
cd gaming-pc-arbitrage

# Install dependencies
npm install

# Build the extension
npm run build

# Run in development mode
npm run dev
```

## 🎯 Quick Start

1. **Configure Settings**
   - Click the extension icon
   - Go to Settings
   - Set your location and preferences

2. **Browse Listings**
   - Navigate to Facebook Marketplace, Craigslist, or OfferUp
   - The extension automatically analyzes visible listings
   - Look for the overlay showing FMV and ROI

3. **Track Deals**
   - Click "Track Deal" on promising listings
   - Manage your pipeline in the Dashboard
   - Use templates for messaging

## 💡 Usage Guide

### Analyzing Listings
The extension automatically parses gaming PC listings when you visit supported sites. Look for:
- **Green overlay**: Good deal (ROI > 20%)
- **Yellow overlay**: Moderate deal (ROI 10-20%)
- **Red overlay**: Poor deal or potential scam

### Keyboard Shortcuts
- `Alt+A`: Analyze current listing
- `Alt+T`: Track current deal
- `Alt+D`: Open dashboard
- `Alt+M`: Open message templates

### Best Practices
1. Always verify listings in person
2. Use secure payment methods
3. Meet in public places
4. Test all components before purchasing
5. Keep detailed records for taxes

## 🔒 Privacy & Security

- **Local-First**: All data stored locally in your browser
- **No Cloud Requirements**: Works offline after initial setup
- **Encrypted Storage**: Sensitive data encrypted at rest
- **ToS Compliant**: Respects platform terms of service
- **No Auto-Messaging**: All messages require user confirmation

## ⚙️ Configuration

### Settings Structure
```json
{
  "location": {
    "zipCode": "12345",
    "maxDistance": 25
  },
  "pricing": {
    "targetROI": 25,
    "minDealValue": 500
  },
  "notifications": {
    "priceDrops": true,
    "newListings": true,
    "dealUpdates": true
  }
}
```

### Feature Flags
Enable/disable features in Settings > Advanced:
- ML Predictions
- OCR Processing
- Voice Commands
- Advanced Analytics

## 📊 Dashboard

Access the dashboard by clicking the extension icon and selecting "Dashboard" or pressing `Alt+D`.

### Available Views
- **Pipeline**: Track deals through stages
- **Inventory**: Manage your current stock
- **Analytics**: Performance metrics and insights
- **P&L**: Profit and loss tracking
- **Settings**: Configure all options

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Run tests
npm test

# Run linting
npm run lint

# Build for production
npm run build

# Create release package
npm run package
```

## 🐛 Troubleshooting

### Extension Not Working
1. Check Chrome version (must be v100+)
2. Ensure extension has required permissions
3. Try reloading the extension
4. Check console for errors (F12)

### Parsing Issues
1. Platform may have updated their layout
2. Submit an issue with the URL
3. Try manual entry as a workaround

### Performance Issues
1. Clear extension cache (Settings > Advanced)
2. Reduce number of tracked deals
3. Disable unused features

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🚨 Disclaimer

This tool is for legitimate business use only. Users are responsible for:
- Compliance with all platform terms of service
- Local laws and regulations
- Tax obligations
- Ethical business practices

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/gaming-pc-arbitrage/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/gaming-pc-arbitrage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/gaming-pc-arbitrage/discussions)

## 🎉 Acknowledgments

Built with:
- Chrome Extension Manifest V3
- React 18 + TypeScript
- Vite + CRXJS
- Tailwind CSS + shadcn/ui
- Dexie.js for IndexedDB
- Zod for validation

---

**Note**: This extension is not affiliated with Facebook, Craigslist, or OfferUp. All trademarks belong to their respective owners.# Updated Mon Aug 11 04:20:20 AM UTC 2025
