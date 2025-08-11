/**
 * Max Auto Engine Demo
 * Run this to see the automation in action
 */

console.log('=== MAX AUTO ENGINE DEMO ===\n');

// Simulate chrome environment
const mockStorage = {
  automationEnabled: false,
  savedSearches: [],
  scannedListings: [],
  automationLogs: []
};

// Mock Chrome APIs for demo
global.chrome = {
  storage: {
    local: {
      get: (keys) => Promise.resolve(
        keys.reduce((acc, key) => ({ ...acc, [key]: mockStorage[key] }), {})
      ),
      set: (data) => {
        Object.assign(mockStorage, data);
        return Promise.resolve();
      }
    }
  },
  runtime: {
    sendMessage: (msg) => {
      console.log(`📡 Message sent: ${msg.type} - ${msg.status || ''}`);
      return Promise.resolve();
    }
  },
  alarms: {
    create: (name, config) => {
      console.log(`⏰ Alarm created: ${name} - every ${config.periodInMinutes} minutes`);
    },
    clear: (name) => {
      console.log(`🚫 Alarm cleared: ${name}`);
    },
    onAlarm: { addListener: () => {} }
  },
  idle: {
    queryState: () => Promise.resolve('idle')
  },
  tabs: {
    create: ({ url, pinned }) => {
      console.log(`📑 Tab created: ${url} (pinned: ${pinned})`);
      return Promise.resolve({ id: 999 });
    },
    remove: (id) => {
      console.log(`❌ Tab closed: ${id}`);
    },
    sendMessage: (tabId, msg) => {
      console.log(`💬 Scan triggered on tab ${tabId}`);
      // Simulate finding some listings
      return Promise.resolve({
        success: true,
        candidates: [
          { id: 'demo-1', title: 'RTX 3080 Gaming PC', price: 1200, roi: 0.35 },
          { id: 'demo-2', title: 'i7-11700K Build', price: 900, roi: 0.28 }
        ]
      });
    },
    onUpdated: { addListener: () => {}, removeListener: () => {} }
  },
  scripting: {
    executeScript: () => Promise.resolve([]),
    insertCSS: () => Promise.resolve([])
  },
  notifications: {
    create: (options) => {
      console.log(`🔔 Notification: ${options.title} - ${options.message}`);
    }
  }
};

async function runDemo() {
  console.log('1️⃣ Starting Max Auto Engine...\n');
  
  const { MaxAutoEngine } = await import('../src/background/maxAutoEngine.js');
  const engine = new MaxAutoEngine();
  
  console.log('2️⃣ Enabling automation...\n');
  await engine.enable();
  
  console.log('\n3️⃣ Adding saved searches...\n');
  
  const searches = [
    {
      id: 'search-fb-1',
      name: 'Facebook RTX 3070+ PCs',
      url: 'https://facebook.com/marketplace/search?query=gaming+pc+rtx+3070',
      platform: 'facebook',
      enabled: true,
      cadenceMinutes: 30,
      createdAt: new Date().toISOString()
    },
    {
      id: 'search-cl-1',
      name: 'Craigslist Gaming Deals',
      url: 'https://craigslist.org/search/sss?query=gaming+pc&max_price=1500',
      platform: 'craigslist',
      enabled: true,
      cadenceMinutes: 60,
      createdAt: new Date().toISOString()
    }
  ];
  
  for (const search of searches) {
    await engine.addSearch(search);
    console.log(`✅ Added: ${search.name}\n`);
  }
  
  console.log('4️⃣ Getting current status...\n');
  const status = await engine.getStatus();
  console.log('Status:', {
    enabled: status.enabled,
    activeSearches: status.activeSearchCount,
    searches: status.searches.map(s => ({ name: s.name, cadence: s.cadenceMinutes }))
  });
  
  console.log('\n5️⃣ Testing a scan (simulated)...\n');
  await engine.testScan('search-fb-1');
  
  console.log('\n6️⃣ Checking logs...\n');
  const logs = await engine.getLogs(5);
  logs.forEach(log => {
    console.log(`📝 ${log.timestamp}: ${log.type} - ${log.searchName || log.searchId}`);
  });
  
  console.log('\n7️⃣ Checking stored results...\n');
  console.log('Scanned listings:', mockStorage.scannedListings);
  
  console.log('\n8️⃣ Pausing a search...\n');
  await engine.pauseSearch('search-cl-1');
  
  console.log('\n9️⃣ Disabling automation...\n');
  await engine.disable();
  
  console.log('\n✅ Demo complete! Max Auto would now:');
  console.log('- Open saved search tabs every 30-60 minutes');
  console.log('- Scan for new listings automatically');
  console.log('- Store high-value candidates');
  console.log('- Send notifications for deals > 30% ROI');
  console.log('- Pause when user is active');
  console.log('- Log all activity for review\n');
}

runDemo().catch(console.error);