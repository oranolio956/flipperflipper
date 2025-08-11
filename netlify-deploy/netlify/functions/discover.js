const axios = require('axios');

// Proxy sources
const PROXY_SOURCES = {
  'proxy-list.download': 'https://www.proxy-list.download/api/v1/get?type=socks5',
  'proxyscrape.com': 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5',
  'github-lists': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
  'proxynova': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/socks5/data.txt'
};

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  // Handle preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const allProxies = [];
    const sources = [];

    // Fetch from each source
    for (const [name, url] of Object.entries(PROXY_SOURCES)) {
      try {
        const response = await axios.get(url, {
          timeout: 5000,
          headers: { 'User-Agent': 'ProxyAssessmentTool/1.0' }
        });

        if (response.data) {
          const text = typeof response.data === 'string' ? response.data : JSON.stringify(response.data);
          const proxies = text.split('\n')
            .filter(line => line.includes(':'))
            .map(line => {
              const [ip, port] = line.trim().split(':');
              return {
                ip,
                port: parseInt(port),
                protocol: 'socks5',
                source: name,
                discovered_at: new Date().toISOString()
              };
            })
            .filter(p => p.ip && p.port && p.port > 0 && p.port < 65536);

          allProxies.push(...proxies);
          sources.push({
            name,
            status: 'success',
            proxy_count: proxies.length
          });
        }
      } catch (error) {
        sources.push({
          name,
          status: 'failed',
          error: error.message
        });
      }
    }

    // Remove duplicates
    const uniqueProxies = Array.from(
      new Map(allProxies.map(p => [`${p.ip}:${p.port}`, p])).values()
    );

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        status: 'success',
        count: uniqueProxies.length,
        sources,
        proxies: uniqueProxies.slice(0, 100) // Limit response size
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        status: 'error',
        message: error.message
      })
    };
  }
};