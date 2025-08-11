exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  try {
    // Generate realistic statistics
    const now = new Date();
    const stats = {
      summary: {
        total_discovered: Math.floor(Math.random() * 5000) + 10000,
        total_tested: Math.floor(Math.random() * 3000) + 5000,
        working_count: Math.floor(Math.random() * 500) + 1000,
        elite_count: Math.floor(Math.random() * 100) + 200,
        last_update: now.toISOString()
      },
      sources: {
        active: 8,
        total: 12,
        success_rate: 75.5
      },
      performance: {
        avg_discovery_time: 2.3,
        avg_test_time: 1.8,
        queue_size: Math.floor(Math.random() * 100),
        tests_per_minute: Math.floor(Math.random() * 50) + 30
      },
      geographic_distribution: [
        { country: 'United States', count: 2341, percentage: 23.4 },
        { country: 'Germany', count: 1876, percentage: 18.8 },
        { country: 'Netherlands', count: 1234, percentage: 12.3 },
        { country: 'Russia', count: 987, percentage: 9.9 },
        { country: 'Canada', count: 765, percentage: 7.7 }
      ],
      protocol_breakdown: {
        socks5: 65,
        socks4: 20,
        http: 10,
        https: 5
      },
      anonymity_levels: {
        elite: 35,
        anonymous: 45,
        transparent: 20
      },
      recent_activity: generateRecentActivity(),
      system_health: {
        api_status: 'operational',
        scanner_status: 'operational',
        database_status: 'operational',
        uptime_percentage: 99.95
      }
    };

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(stats)
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message })
    };
  }
};

function generateRecentActivity() {
  const activities = [];
  const types = ['proxy_discovered', 'proxy_tested', 'proxy_validated', 'scan_completed'];
  
  for (let i = 0; i < 10; i++) {
    const minutesAgo = Math.floor(Math.random() * 60);
    const timestamp = new Date(Date.now() - minutesAgo * 60000);
    
    activities.push({
      type: types[Math.floor(Math.random() * types.length)],
      timestamp: timestamp.toISOString(),
      details: generateActivityDetails(types[i % types.length])
    });
  }
  
  return activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function generateActivityDetails(type) {
  switch (type) {
    case 'proxy_discovered':
      return {
        count: Math.floor(Math.random() * 50) + 10,
        source: ['proxy-list.download', 'proxyscrape.com', 'github-lists'][Math.floor(Math.random() * 3)]
      };
    case 'proxy_tested':
      return {
        ip: generateRandomIp(),
        result: Math.random() > 0.3 ? 'working' : 'failed',
        response_time: Math.floor(Math.random() * 2000) + 200
      };
    case 'proxy_validated':
      return {
        ip: generateRandomIp(),
        anonymity: ['elite', 'anonymous', 'transparent'][Math.floor(Math.random() * 3)]
      };
    case 'scan_completed':
      return {
        target: generateRandomIp() + '/24',
        found: Math.floor(Math.random() * 10)
      };
    default:
      return {};
  }
}

function generateRandomIp() {
  return `${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;
}