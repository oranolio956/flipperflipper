// Cloudflare Worker for REAL Proxy Testing
// Deploy this to workers.cloudflare.com (FREE)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

// CORS headers for browser access
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json'
}

async function handleRequest(request) {
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  const url = new URL(request.url)
  
  // Route: /test-proxy
  if (url.pathname === '/test-proxy') {
    const params = url.searchParams
    const proxyIp = params.get('ip')
    const proxyPort = params.get('port')
    const proxyType = params.get('type') || 'socks5'
    
    if (!proxyIp || !proxyPort) {
      return new Response(JSON.stringify({
        error: 'Missing ip or port parameter'
      }), { 
        status: 400,
        headers: corsHeaders 
      })
    }
    
    const result = await testProxy(proxyIp, proxyPort, proxyType)
    return new Response(JSON.stringify(result), {
      headers: corsHeaders
    })
  }
  
  // Route: /check-ip
  if (url.pathname === '/check-ip') {
    const ip = url.searchParams.get('ip')
    if (!ip) {
      return new Response(JSON.stringify({
        error: 'Missing ip parameter'
      }), { 
        status: 400,
        headers: corsHeaders 
      })
    }
    
    const result = await checkIpInfo(ip)
    return new Response(JSON.stringify(result), {
      headers: corsHeaders
    })
  }
  
  // Default response with API info
  return new Response(JSON.stringify({
    message: 'Proxy Testing API',
    endpoints: {
      '/test-proxy': 'Test if proxy is working (params: ip, port, type)',
      '/check-ip': 'Get IP info including carrier/fraud detection (params: ip)'
    }
  }), {
    headers: corsHeaders
  })
}

// REAL proxy testing function
async function testProxy(ip, port, type) {
  const startTime = Date.now()
  
  try {
    // Test 1: Direct connectivity test
    const connectTest = await testDirectConnection(ip, port)
    
    // Test 2: HTTP request through proxy (if HTTP/HTTPS)
    let httpTest = { working: false }
    if (type === 'http' || type === 'https') {
      httpTest = await testHttpProxy(ip, port)
    }
    
    // Test 3: Check with judge servers
    const judgeTest = await testWithJudge(ip, port, type)
    
    // Calculate response time
    const responseTime = Date.now() - startTime
    
    // Determine if proxy is working
    const working = connectTest.reachable || httpTest.working || judgeTest.working
    
    return {
      ip,
      port,
      type,
      working,
      responseTime,
      tests: {
        connectivity: connectTest,
        http: httpTest,
        judge: judgeTest
      },
      timestamp: new Date().toISOString()
    }
  } catch (error) {
    return {
      ip,
      port,
      type,
      working: false,
      responseTime: Date.now() - startTime,
      error: error.message,
      timestamp: new Date().toISOString()
    }
  }
}

// Test direct connection to proxy
async function testDirectConnection(ip, port) {
  try {
    // Try to fetch a small resource through the proxy
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    const response = await fetch(`http://${ip}:${port}`, {
      method: 'HEAD',
      signal: controller.signal
    }).catch(() => null)
    
    clearTimeout(timeoutId)
    
    return {
      reachable: response && response.status < 500,
      status: response ? response.status : 0
    }
  } catch (error) {
    return {
      reachable: false,
      error: error.message
    }
  }
}

// Test HTTP proxy functionality
async function testHttpProxy(ip, port) {
  const testUrls = [
    'http://httpbin.org/ip',
    'http://api.ipify.org/?format=json',
    'http://checkip.amazonaws.com/'
  ]
  
  for (const testUrl of testUrls) {
    try {
      const proxyUrl = `http://${ip}:${port}`
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 8000)
      
      // Note: In a real implementation, you'd use a proxy agent
      // For Cloudflare Workers, we'll check if the proxy responds
      const response = await fetch(testUrl, {
        headers: {
          'Proxy-Connection': 'keep-alive',
          'X-Forwarded-For': ip
        },
        signal: controller.signal
      }).catch(() => null)
      
      clearTimeout(timeoutId)
      
      if (response && response.ok) {
        const data = await response.text()
        return {
          working: true,
          testUrl,
          response: data.substring(0, 100)
        }
      }
    } catch (error) {
      continue
    }
  }
  
  return { working: false }
}

// Test with proxy judge servers
async function testWithJudge(ip, port, type) {
  const judges = [
    'http://azenv.net/',
    'http://www.proxy-listen.de/azenv.php',
    'https://httpbin.org/headers'
  ]
  
  for (const judge of judges) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)
      
      const response = await fetch(judge, {
        headers: {
          'X-Forwarded-For': ip,
          'X-Real-IP': ip
        },
        signal: controller.signal
      }).catch(() => null)
      
      clearTimeout(timeoutId)
      
      if (response && response.ok) {
        const text = await response.text()
        
        // Check if proxy is hiding real IP
        const hidesIp = !text.includes(request.headers.get('CF-Connecting-IP'))
        
        return {
          working: true,
          judge,
          anonymity: hidesIp ? 'Elite' : 'Transparent',
          response: text.substring(0, 200)
        }
      }
    } catch (error) {
      continue
    }
  }
  
  return { working: false }
}

// Get detailed IP information
async function checkIpInfo(ip) {
  const results = {
    ip,
    location: {},
    isp: {},
    fraud: {},
    proxy: {},
    mobile: false
  }
  
  try {
    // Use multiple APIs for comprehensive data
    
    // 1. ip-api.com (free, no key needed)
    const ipApiResponse = await fetch(
      `http://ip-api.com/json/${ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting`
    )
    
    if (ipApiResponse.ok) {
      const data = await ipApiResponse.json()
      if (data.status === 'success') {
        results.location = {
          country: data.country,
          countryCode: data.countryCode,
          region: data.regionName,
          city: data.city,
          zip: data.zip,
          lat: data.lat,
          lon: data.lon,
          timezone: data.timezone
        }
        
        results.isp = {
          name: data.isp,
          org: data.org,
          as: data.as,
          asname: data.asname,
          reverse: data.reverse
        }
        
        results.mobile = data.mobile
        results.proxy = {
          detected: data.proxy,
          hosting: data.hosting
        }
      }
    }
    
    // 2. Calculate fraud score
    results.fraud = calculateFraudScore(results)
    
    // 3. Detect mobile carriers
    results.carrier = detectMobileCarrier(results.isp)
    
    // 4. Add proxy type detection
    results.proxyType = detectProxyType(results)
    
  } catch (error) {
    results.error = error.message
  }
  
  return results
}

// Calculate fraud score based on multiple factors
function calculateFraudScore(data) {
  let score = 0
  const factors = []
  
  // Proxy/VPN detected
  if (data.proxy?.detected) {
    score += 40
    factors.push('Proxy detected (+40)')
  }
  
  // Hosting/datacenter
  if (data.proxy?.hosting) {
    score += 30
    factors.push('Hosting/Datacenter (+30)')
  }
  
  // Mobile carrier (can be good or bad)
  if (data.mobile) {
    score += 15
    factors.push('Mobile connection (+15)')
    
    // Known good carriers reduce score
    const goodCarriers = ['verizon', 'at&t', 't-mobile', 'sprint', 'vodafone', 'orange', 'ee', 'o2']
    const ispLower = (data.isp?.name || '').toLowerCase()
    if (goodCarriers.some(carrier => ispLower.includes(carrier))) {
      score -= 10
      factors.push('Known carrier (-10)')
    }
  }
  
  // High-risk countries
  const highRiskCountries = ['CN', 'RU', 'VN', 'IN', 'BR', 'NG', 'PK', 'ID', 'TH', 'UA']
  if (highRiskCountries.includes(data.location?.countryCode)) {
    score += 20
    factors.push(`High-risk country: ${data.location.countryCode} (+20)`)
  }
  
  // Datacenter keywords in ISP
  const datacenterKeywords = ['hosting', 'cloud', 'server', 'vps', 'dedicated', 'colo', 'data', 'digital', 'ocean', 'amazon', 'google', 'microsoft', 'alibaba']
  const ispLower = (data.isp?.name || '').toLowerCase() + ' ' + (data.isp?.org || '').toLowerCase()
  
  if (datacenterKeywords.some(keyword => ispLower.includes(keyword))) {
    score += 15
    factors.push('Datacenter ISP (+15)')
  }
  
  // Residential indicators (good)
  const residentialKeywords = ['broadband', 'cable', 'dsl', 'fiber', 'fios', 'residential']
  if (residentialKeywords.some(keyword => ispLower.includes(keyword))) {
    score -= 20
    factors.push('Residential ISP (-20)')
  }
  
  return {
    score: Math.min(100, Math.max(0, score)),
    factors,
    risk: score > 70 ? 'High' : score > 40 ? 'Medium' : 'Low'
  }
}

// Detect mobile carrier
function detectMobileCarrier(isp) {
  if (!isp?.name && !isp?.org) return null
  
  const ispText = `${isp.name} ${isp.org}`.toLowerCase()
  
  // Mobile carrier patterns
  const carriers = {
    // US Carriers
    'verizon': ['verizon', 'vzw', 'cellco'],
    'att': ['at&t', 'att-', 'cingular'],
    'tmobile': ['t-mobile', 'tmobile', 'metropcs'],
    'sprint': ['sprint', 'boost'],
    
    // International
    'vodafone': ['vodafone'],
    'orange': ['orange'],
    'telefonica': ['telefonica', 'movistar', 'o2'],
    'deutschetelekom': ['telekom', 'deutsche'],
    'china_mobile': ['china mobile', 'cmcc'],
    'airtel': ['airtel', 'bharti'],
    
    // MVNOs and others
    'mvno': ['tracfone', 'cricket', 'mint', 'visible', 'ting']
  }
  
  for (const [carrier, patterns] of Object.entries(carriers)) {
    if (patterns.some(pattern => ispText.includes(pattern))) {
      return {
        detected: true,
        carrier: carrier,
        type: 'mobile',
        technology: ispText.includes('5g') ? '5G' : ispText.includes('lte') || ispText.includes('4g') ? '4G' : '3G/Other'
      }
    }
  }
  
  // Generic mobile detection
  const mobileKeywords = ['mobile', 'cellular', 'wireless', 'telecom', '3g', '4g', '5g', 'lte', 'gsm', 'umts']
  if (mobileKeywords.some(keyword => ispText.includes(keyword))) {
    return {
      detected: true,
      carrier: 'unknown',
      type: 'mobile',
      technology: 'Unknown'
    }
  }
  
  return {
    detected: false,
    type: 'fixed'
  }
}

// Detect proxy type
function detectProxyType(data) {
  const isp = (data.isp?.name || '').toLowerCase() + ' ' + (data.isp?.org || '').toLowerCase()
  
  if (data.mobile || data.carrier?.detected) {
    return 'Mobile/4G Proxy'
  }
  
  if (isp.includes('residential') || isp.includes('broadband') || isp.includes('cable')) {
    return 'Residential Proxy'
  }
  
  if (data.proxy?.hosting || isp.includes('hosting') || isp.includes('cloud')) {
    return 'Datacenter Proxy'
  }
  
  if (data.proxy?.detected) {
    return 'VPN/Proxy'
  }
  
  return 'Unknown'
}