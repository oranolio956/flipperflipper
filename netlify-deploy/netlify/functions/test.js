const axios = require('axios');
const net = require('net');
const { promisify } = require('util');

// Test judges for checking proxy functionality
const TEST_JUDGES = [
  'http://httpbin.org/ip',
  'http://api.ipify.org/?format=json',
  'http://checkip.amazonaws.com/'
];

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  try {
    const body = JSON.parse(event.body || '{}');
    const { proxy } = body;
    
    if (!proxy || !proxy.ip || !proxy.port) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Invalid proxy data' })
      };
    }

    // Test proxy connectivity
    const startTime = Date.now();
    const testResult = await testProxyConnection(proxy);
    const responseTime = Date.now() - startTime;

    // Get geolocation data
    const geoData = await getGeoLocation(proxy.ip);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        ...proxy,
        working: testResult.working,
        anonymity_level: testResult.anonymity || 'unknown',
        response_time: responseTime,
        country: geoData.country || 'Unknown',
        country_code: geoData.country_code || 'XX',
        city: geoData.city || 'Unknown',
        region: geoData.region || 'Unknown',
        isp: geoData.isp || 'Unknown',
        asn: geoData.asn || 'Unknown',
        is_mobile: geoData.is_mobile || false,
        is_hosting: geoData.is_hosting || false,
        fraud_score: calculateFraudScore(geoData),
        tested_at: new Date().toISOString()
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message })
    };
  }
};

async function testProxyConnection(proxy) {
  // For SOCKS5, we'll do a basic TCP connection test
  if (proxy.protocol === 'socks5') {
    return await testSocks5Basic(proxy.ip, proxy.port);
  }
  
  // For HTTP/HTTPS proxies
  return await testHttpProxy(proxy);
}

async function testSocks5Basic(ip, port) {
  return new Promise((resolve) => {
    const client = new net.Socket();
    const timeout = setTimeout(() => {
      client.destroy();
      resolve({ working: false });
    }, 5000);

    client.connect(port, ip, () => {
      clearTimeout(timeout);
      // Send SOCKS5 greeting
      client.write(Buffer.from([0x05, 0x01, 0x00]));
    });

    client.on('data', (data) => {
      if (data[0] === 0x05 && data[1] === 0x00) {
        // SOCKS5 server responded positively
        client.destroy();
        resolve({ working: true, anonymity: 'elite' });
      } else {
        client.destroy();
        resolve({ working: false });
      }
    });

    client.on('error', () => {
      clearTimeout(timeout);
      resolve({ working: false });
    });
  });
}

async function testHttpProxy(proxy) {
  try {
    const proxyUrl = `http://${proxy.ip}:${proxy.port}`;
    const response = await axios.get(TEST_JUDGES[0], {
      proxy: {
        host: proxy.ip,
        port: proxy.port
      },
      timeout: 5000
    });

    if (response.data) {
      const realIp = extractIp(response.data);
      const anonymity = realIp === proxy.ip ? 'transparent' : 'anonymous';
      return { working: true, anonymity };
    }
  } catch (error) {
    // Proxy failed
  }
  return { working: false };
}

async function getGeoLocation(ip) {
  try {
    const response = await axios.get(`http://ip-api.com/json/${ip}?fields=status,country,countryCode,region,city,isp,org,as,mobile,hosting,proxy`, {
      timeout: 3000
    });
    
    if (response.data && response.data.status === 'success') {
      return {
        country: response.data.country,
        country_code: response.data.countryCode,
        region: response.data.region,
        city: response.data.city,
        isp: response.data.isp,
        asn: response.data.as,
        is_mobile: response.data.mobile || false,
        is_hosting: response.data.hosting || false,
        is_proxy: response.data.proxy || false
      };
    }
  } catch (error) {
    // Fallback to basic data
  }
  
  return {
    country: 'Unknown',
    country_code: 'XX',
    city: 'Unknown',
    region: 'Unknown'
  };
}

function calculateFraudScore(geoData) {
  let score = 0;
  
  if (geoData.is_hosting) score += 30;
  if (geoData.is_proxy) score += 20;
  if (geoData.is_mobile) score += 10;
  if (geoData.country_code === 'XX') score += 25;
  if (!geoData.isp || geoData.isp === 'Unknown') score += 15;
  
  return Math.min(score, 100);
}

function extractIp(text) {
  const match = text.match(/\d+\.\d+\.\d+\.\d+/);
  return match ? match[0] : null;
}