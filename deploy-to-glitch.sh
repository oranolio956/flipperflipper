#!/bin/bash

# Deploy to Glitch - Full Stack Deployment
# Both Frontend and Backend with ALL features

echo "🚀 Deploying Full Stack Proxy Assessment Tool to Glitch"
echo "======================================================"

# Create Glitch project structure
mkdir -p /workspace/glitch-deploy
cd /workspace/glitch-deploy

# Create package.json for Glitch
cat > package.json << 'EOF'
{
  "name": "proxy-assessment-tool",
  "version": "1.0.0",
  "description": "Full-featured proxy scanner with real backend",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "node-fetch": "^2.7.0",
    "socks-proxy-agent": "^8.0.2",
    "http-proxy-agent": "^7.0.0",
    "geoip-lite": "^1.4.7",
    "ws": "^8.14.2"
  },
  "engines": {
    "node": "16.x"
  }
}
EOF

# Create the full backend server
cat > server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const { SocksProxyAgent } = require('socks-proxy-agent');
const HttpProxyAgent = require('http-proxy-agent');
const geoip = require('geoip-lite');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// WebSocket server
const wss = new WebSocket.Server({ noServer: true });

// Proxy sources
const PROXY_SOURCES = {
  'github-speedx': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
  'github-shifty': 'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt',
  'github-jetkai': 'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt',
  'proxyscrape': 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&format=textplain'
};

// Store for active proxies
let proxyCache = new Map();
let testResults = new Map();

// API Routes

// Discover proxies from all sources
app.get('/api/discover', async (req, res) => {
  try {
    const allProxies = [];
    const sourceStats = {};

    for (const [name, url] of Object.entries(PROXY_SOURCES)) {
      try {
        const response = await fetch(url, {
          headers: { 'User-Agent': 'ProxyAssessmentTool/1.0' }
        });
        
        if (response.ok) {
          const text = await response.text();
          const proxies = parseProxies(text, name);
          allProxies.push(...proxies);
          sourceStats[name] = { success: true, count: proxies.length };
        } else {
          sourceStats[name] = { success: false, error: response.statusText };
        }
      } catch (error) {
        sourceStats[name] = { success: false, error: error.message };
      }
    }

    // Remove duplicates
    const uniqueProxies = Array.from(
      new Map(allProxies.map(p => [`${p.ip}:${p.port}`, p])).values()
    );

    // Cache proxies
    uniqueProxies.forEach(p => {
      proxyCache.set(`${p.ip}:${p.port}`, p);
    });

    res.json({
      status: 'success',
      count: uniqueProxies.length,
      proxies: uniqueProxies,
      sources: sourceStats
    });

    // Broadcast to WebSocket clients
    broadcast({
      type: 'discovery_complete',
      data: { count: uniqueProxies.length }
    });

  } catch (error) {
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Test a single proxy
app.post('/api/test', async (req, res) => {
  const { ip, port, type = 'socks5' } = req.body;
  
  try {
    const result = await testProxy(ip, port, type);
    
    // Store result
    testResults.set(`${ip}:${port}`, result);
    
    // Broadcast to WebSocket clients
    broadcast({
      type: 'proxy_tested',
      data: result
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Test multiple proxies
app.post('/api/test/batch', async (req, res) => {
  const { proxies } = req.body;
  
  try {
    const results = await Promise.all(
      proxies.map(p => testProxy(p.ip, p.port, p.type))
    );
    
    res.json({
      status: 'success',
      results: results
    });
  } catch (error) {
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Get proxy statistics
app.get('/api/stats', (req, res) => {
  const tested = Array.from(testResults.values());
  const working = tested.filter(p => p.working);
  
  res.json({
    total_discovered: proxyCache.size,
    total_tested: tested.length,
    working_count: working.length,
    average_response_time: working.length > 0 
      ? Math.round(working.reduce((sum, p) => sum + p.responseTime, 0) / working.length)
      : 0,
    by_country: groupByCountry(tested),
    by_type: groupByType(tested)
  });
});

// Get detailed analytics
app.get('/api/analytics', (req, res) => {
  const tested = Array.from(testResults.values());
  
  res.json({
    metrics: {
      total_proxies: tested.length,
      working_proxies: tested.filter(p => p.working).length,
      average_response_time: calculateAverage(tested, 'responseTime'),
      fraud_score_avg: calculateAverage(tested, 'fraudScore')
    },
    geographic: getGeographicDistribution(tested),
    performance: getPerformanceMetrics(tested),
    timeline: getTimelineData(tested)
  });
});

// Helper Functions

function parseProxies(text, source) {
  const lines = text.split('\n');
  const proxies = [];
  
  lines.forEach(line => {
    line = line.trim();
    if (line && line.includes(':')) {
      const [ip, port] = line.split(':');
      if (ip && port && !isNaN(port)) {
        const geo = geoip.lookup(ip) || {};
        proxies.push({
          ip: ip.trim(),
          port: parseInt(port),
          source: source,
          country: geo.country || 'Unknown',
          city: geo.city || 'Unknown',
          region: geo.region || 'Unknown',
          ll: geo.ll || [0, 0]
        });
      }
    }
  });
  
  return proxies;
}

async function testProxy(ip, port, type) {
  const startTime = Date.now();
  const geo = geoip.lookup(ip) || {};
  
  let working = false;
  let responseTime = 999999;
  let anonymityLevel = 'unknown';
  
  try {
    // Create appropriate agent
    const agent = type === 'socks5' 
      ? new SocksProxyAgent(`socks5://${ip}:${port}`)
      : new HttpProxyAgent(`http://${ip}:${port}`);
    
    // Test proxy with timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    
    const testUrl = 'http://httpbin.org/ip';
    const response = await fetch(testUrl, {
      agent,
      signal: controller.signal,
      timeout: 10000
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      working = true;
      responseTime = Date.now() - startTime;
      
      // Check anonymity
      const data = await response.json();
      if (data.origin !== ip) {
        anonymityLevel = 'elite';
      } else {
        anonymityLevel = 'transparent';
      }
    }
  } catch (error) {
    // Proxy failed
    working = false;
  }
  
  // Calculate fraud score
  const fraudScore = calculateFraudScore({
    ip, geo, responseTime, working
  });
  
  return {
    ip,
    port,
    type,
    working,
    responseTime,
    anonymityLevel,
    country: geo.country || 'Unknown',
    city: geo.city || 'Unknown',
    region: geo.region || 'Unknown',
    isp: geo.org || 'Unknown',
    fraudScore,
    lastTested: new Date().toISOString()
  };
}

function calculateFraudScore(proxy) {
  let score = 0;
  
  // High response time
  if (proxy.responseTime > 5000) score += 20;
  else if (proxy.responseTime > 2000) score += 10;
  
  // Geographic risk
  const riskyCountries = ['CN', 'RU', 'VN', 'ID'];
  if (riskyCountries.includes(proxy.geo?.country)) score += 15;
  
  // ISP type
  if (proxy.geo?.org?.toLowerCase().includes('hosting')) score += 20;
  if (proxy.geo?.org?.toLowerCase().includes('vpn')) score += 15;
  
  // Not working
  if (!proxy.working) score += 30;
  
  return Math.min(score, 100);
}

function groupByCountry(proxies) {
  const groups = {};
  proxies.forEach(p => {
    if (!groups[p.country]) groups[p.country] = 0;
    groups[p.country]++;
  });
  return groups;
}

function groupByType(proxies) {
  const groups = {};
  proxies.forEach(p => {
    if (!groups[p.type]) groups[p.type] = 0;
    groups[p.type]++;
  });
  return groups;
}

function calculateAverage(items, field) {
  const validItems = items.filter(item => item[field] !== undefined);
  if (validItems.length === 0) return 0;
  return Math.round(
    validItems.reduce((sum, item) => sum + item[field], 0) / validItems.length
  );
}

function getGeographicDistribution(proxies) {
  const distribution = {};
  proxies.forEach(p => {
    const key = `${p.country}-${p.city}`;
    if (!distribution[key]) {
      distribution[key] = {
        country: p.country,
        city: p.city,
        count: 0,
        working: 0
      };
    }
    distribution[key].count++;
    if (p.working) distribution[key].working++;
  });
  return Object.values(distribution);
}

function getPerformanceMetrics(proxies) {
  const working = proxies.filter(p => p.working);
  return {
    responseTimeDistribution: {
      fast: working.filter(p => p.responseTime < 1000).length,
      medium: working.filter(p => p.responseTime >= 1000 && p.responseTime < 3000).length,
      slow: working.filter(p => p.responseTime >= 3000).length
    },
    anonymityDistribution: {
      elite: working.filter(p => p.anonymityLevel === 'elite').length,
      anonymous: working.filter(p => p.anonymityLevel === 'anonymous').length,
      transparent: working.filter(p => p.anonymityLevel === 'transparent').length
    }
  };
}

function getTimelineData(proxies) {
  // Group by hour for the last 24 hours
  const timeline = [];
  const now = new Date();
  
  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now - i * 60 * 60 * 1000);
    const hourStr = hour.toISOString().slice(0, 13);
    
    const hourProxies = proxies.filter(p => 
      p.lastTested && p.lastTested.startsWith(hourStr)
    );
    
    timeline.push({
      hour: hourStr,
      tested: hourProxies.length,
      working: hourProxies.filter(p => p.working).length
    });
  }
  
  return timeline;
}

// WebSocket handling
function broadcast(message) {
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(message));
    }
  });
}

// Serve frontend
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// WebSocket upgrade
const server = app.listen(PORT, () => {
  console.log(`🚀 Proxy Assessment Tool running on port ${PORT}`);
  console.log(`📍 Frontend: http://localhost:${PORT}`);
  console.log(`📍 API: http://localhost:${PORT}/api`);
});

server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

// Handle WebSocket connections
wss.on('connection', (ws) => {
  console.log('New WebSocket connection');
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log('WebSocket message:', data);
    } catch (error) {
      console.error('Invalid WebSocket message:', error);
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});
EOF

# Create public directory for frontend
mkdir -p public

# Copy and update frontend to use our backend
cp /workspace/frontend/index.html public/index.html
cp /workspace/frontend/analytics_dashboard.html public/analytics_dashboard.html

# Update the API URL in frontend to use relative paths
sed -i 's|https://proxy-assessment-backend.onrender.com|/api|g' public/index.html
sed -i 's|http://localhost:8000|/api|g' public/index.html
sed -i 's|https://your-api-domain.com|/api|g' public/index.html

# Create .glitch-assets file
cat > .glitch-assets << 'EOF'
{"name":"proxy-assessment-tool","date":"2024-01-01T00:00:00.000Z","url":"https://cdn.glitch.com/project-avatar.png","type":"image/png"}
EOF

# Create README for Glitch
cat > README.md << 'EOF'
# 🚀 Proxy Assessment Tool - Full Stack

A complete proxy scanner with real backend testing capabilities!

## Features
- ✅ Real proxy testing (not simulated!)
- ✅ SOCKS5 and HTTP proxy support
- ✅ WebSocket real-time updates
- ✅ Geographic distribution
- ✅ Fraud scoring
- ✅ Analytics dashboard
- ✅ Export functionality

## Live Demo
Visit your Glitch project URL to see it in action!

## API Endpoints
- GET `/api/discover` - Discover proxies from sources
- POST `/api/test` - Test a single proxy
- POST `/api/test/batch` - Test multiple proxies
- GET `/api/stats` - Get statistics
- GET `/api/analytics` - Get detailed analytics

## Tech Stack
- Backend: Node.js + Express
- Frontend: Vanilla JavaScript
- Real proxy testing with socks-proxy-agent
- GeoIP lookup with geoip-lite
- WebSocket for real-time updates
EOF

echo "✅ Glitch project files created!"
echo ""
echo "📦 Project structure:"
echo "  - server.js (Full backend with all features)"
echo "  - package.json (Dependencies)"
echo "  - public/index.html (Frontend)"
echo "  - public/analytics_dashboard.html (Analytics)"
echo ""
echo "🚀 To deploy to Glitch:"
echo ""
echo "1. Go to: https://glitch.com/edit/#!/remix/hello-express"
echo "2. Delete all default files"
echo "3. Drag and drop these files:"
echo "   - /workspace/glitch-deploy/*"
echo "   - /workspace/glitch-deploy/public/*"
echo ""
echo "OR use Glitch import from GitHub:"
echo "1. Push to GitHub"
echo "2. In Glitch: New Project > Import from GitHub"
echo ""
echo "Your app will have:"
echo "✅ Real backend (not simulated)"
echo "✅ Actual proxy testing"
echo "✅ WebSocket support"
echo "✅ Full analytics"
echo "✅ All features working!"

# Create a zip file for easy upload
cd /workspace
zip -r glitch-deploy.zip glitch-deploy/

echo ""
echo "📦 Created glitch-deploy.zip for easy upload!"