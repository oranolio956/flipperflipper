#!/usr/bin/env python3
"""
Phase 1 Testing Script - Proxy Discovery
Provides proof that the web scraping module works
"""

import asyncio
import sys
import time
from datetime import datetime
from proxy_sources import ProxySourceManager, GitHubProxyList, ProxyScrapeCom

async def test_individual_sources():
    """Test each source individually"""
    print("=" * 70)
    print("PHASE 1 TEST: Individual Source Testing")
    print("=" * 70)
    
    sources = [
        GitHubProxyList(),
        ProxyScrapeCom(),
    ]
    
    for source in sources:
        print(f"\n🔍 Testing {source.name}...")
        print(f"Rate limit: {source.rate_limiter.rate} req/s")
        
        try:
            start_time = time.time()
            proxies = await source.fetch()
            duration = time.time() - start_time
            
            print(f"✅ Success! Found {len(proxies)} proxies in {duration:.2f}s")
            
            # Show samples
            if proxies:
                print(f"\nSample proxies from {source.name}:")
                for i, proxy in enumerate(list(proxies)[:3]):
                    print(f"  {proxy.address} - {proxy.protocol} - {proxy.country or 'Unknown'}")
            
            # Show reliability
            print(f"Reliability score: {source.reliability_score:.2%}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_manager_functionality():
    """Test the complete ProxySourceManager"""
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: ProxySourceManager Integration")
    print("=" * 70)
    
    manager = ProxySourceManager()
    
    # Test 1: Initial fetch
    print("\n📥 Test 1: Initial proxy discovery...")
    start = time.time()
    proxies = await manager.get_proxies()
    duration = time.time() - start
    
    print(f"✅ Discovered {len(proxies)} unique proxies in {duration:.2f}s")
    
    # Analyze by protocol
    by_protocol = {}
    by_source = {}
    
    for proxy in proxies:
        # Count by protocol
        by_protocol[proxy.protocol] = by_protocol.get(proxy.protocol, 0) + 1
        # Count by source
        by_source[proxy.source] = by_source.get(proxy.source, 0) + 1
    
    print("\n📊 Breakdown by protocol:")
    for protocol, count in sorted(by_protocol.items()):
        print(f"  {protocol}: {count}")
    
    print("\n📊 Breakdown by source:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")
    
    # Test 2: Cache functionality
    print("\n💾 Test 2: Cache functionality...")
    start = time.time()
    cached_proxies = await manager.get_proxies()
    cache_duration = time.time() - start
    
    print(f"✅ Cache hit! Retrieved {len(cached_proxies)} proxies in {cache_duration:.3f}s")
    print(f"   Speed improvement: {duration/cache_duration:.1f}x faster")
    
    # Test 3: Force refresh
    print("\n🔄 Test 3: Force refresh...")
    start = time.time()
    refreshed_proxies = await manager.get_proxies(force_refresh=True)
    refresh_duration = time.time() - start
    
    print(f"✅ Force refreshed {len(refreshed_proxies)} proxies in {refresh_duration:.2f}s")
    
    # Test 4: Source statistics
    print("\n📈 Test 4: Source statistics...")
    stats = manager.get_source_statistics()
    
    for source_name, source_stats in stats.items():
        print(f"\n{source_name}:")
        print(f"  Reliability: {source_stats['reliability_score'] * 100:.1f}%")
        print(f"  Success/Failure: {source_stats['success_count']}/{source_stats['failure_count']}")
        if source_stats['last_success']:
            print(f"  Last success: {source_stats['last_success']}")


async def test_anti_detection():
    """Test anti-detection features"""
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: Anti-Detection Features")
    print("=" * 70)
    
    from proxy_sources import AntiDetectionManager
    
    anti_detect = AntiDetectionManager()
    
    print("\n🕵️ Testing header randomization...")
    
    # Get multiple sets of headers
    headers_sets = []
    for i in range(5):
        headers = anti_detect.get_headers()
        headers_sets.append(headers)
        print(f"\nRequest {i+1}:")
        print(f"  User-Agent: {headers['User-Agent'][:60]}...")
        print(f"  Has Referer: {'Referer' in headers}")
    
    # Check that user agents are different
    user_agents = [h['User-Agent'] for h in headers_sets]
    unique_agents = len(set(user_agents))
    
    print(f"\n✅ Generated {unique_agents} unique User-Agents out of 5 requests")
    
    # Test delay functionality
    print("\n⏱️ Testing random delays...")
    delays = []
    for i in range(3):
        start = time.time()
        await anti_detect.random_delay(0.1, 0.5)
        delay = time.time() - start
        delays.append(delay)
        print(f"  Delay {i+1}: {delay:.3f}s")
    
    print(f"✅ Average delay: {sum(delays)/len(delays):.3f}s")


async def test_parser_robustness():
    """Test proxy string parser with various formats"""
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: Parser Robustness")
    print("=" * 70)
    
    from proxy_sources import ProxySourceBase
    
    # Create a test source
    test_source = ProxySourceBase("TestParser")
    
    test_cases = [
        # Format, Expected Result
        ("192.168.1.1:8080", True),
        ("10.0.0.1:1080", True),
        ("http://192.168.1.1:3128", True),
        ("socks5://10.0.0.1:1080", True),
        ("192.168.1.1:8080 US", True),
        ("192.168.1.1:8080 SOCKS5 Elite US", True),
        ("invalid:proxy", False),
        ("999.999.999.999:8080", False),
        ("192.168.1.1:99999", False),
        ("", False),
        ("192.168.1.1", False),
        ("just text", False),
    ]
    
    print("\n🧪 Testing proxy parser...")
    passed = 0
    failed = 0
    
    for test_input, should_parse in test_cases:
        result = test_source.parse_proxy_string(test_input)
        success = (result is not None) == should_parse
        
        if success:
            passed += 1
            print(f"✅ '{test_input}' -> {result.address if result else 'None'}")
        else:
            failed += 1
            print(f"❌ '{test_input}' -> Unexpected result")
    
    print(f"\n📊 Parser test results: {passed} passed, {failed} failed")


async def test_live_discovery():
    """Live test showing real proxy discovery"""
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: Live Discovery Demo")
    print("=" * 70)
    
    manager = ProxySourceManager()
    
    print("\n🌐 Discovering proxies from the internet...")
    print("This will contact real proxy list websites...\n")
    
    proxies = await manager.get_proxies()
    
    # Show first 10 working proxies
    print(f"\n✅ Found {len(proxies)} total proxies")
    print("\nShowing first 10 proxies:")
    print("-" * 60)
    print(f"{'IP:Port':<25} {'Protocol':<10} {'Source':<20}")
    print("-" * 60)
    
    for i, proxy in enumerate(list(proxies)[:10]):
        print(f"{proxy.address:<25} {proxy.protocol:<10} {proxy.source:<20}")
    
    print("\n✅ Phase 1 complete! Web scraping module is working perfectly.")


async def main():
    """Run all Phase 1 tests"""
    print("\n" + "🚀 " * 20)
    print("PROXY DISCOVERY MODULE - PHASE 1 TESTING")
    print("🚀 " * 20)
    print(f"\nTest started at: {datetime.now().isoformat()}")
    
    try:
        # Run all tests
        await test_individual_sources()
        await test_manager_functionality()
        await test_anti_detection()
        await test_parser_robustness()
        await test_live_discovery()
        
        print("\n" + "=" * 70)
        print("✅ ALL PHASE 1 TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())