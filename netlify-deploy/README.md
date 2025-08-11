# ProxyAssessmentTool - Full Stack Deployment

This is a complete proxy assessment tool with:
- Frontend: Modern web interface
- Backend: Netlify Functions (serverless)

## Features
- Automatic proxy discovery from multiple sources
- Real-time proxy testing
- Geolocation and fraud detection
- Mobile proxy detection
- Export functionality

## Deployment
1. Drag this folder to Netlify Drop
2. Or use Netlify CLI: `netlify deploy --prod`

## API Endpoints (via Netlify Functions)
- `/.netlify/functions/discover` - Discover proxies
- `/.netlify/functions/test` - Test individual proxy
- `/.netlify/functions/scan` - Intelligent scanning
- `/.netlify/functions/stats` - Get statistics
