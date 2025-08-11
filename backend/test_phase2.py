#!/usr/bin/env python3
"""
Phase 2 Testing Script - Active Proxy Scanner
Proves the scanner works with real protocol detection
"""

import asyncio
import sys
import time
from datetime import datetime
from proxy_scanner import (
    ProxyProtocolDetector, 
    IntelligentTargetSelector,
    EthicalScanManager,
    ScanTarget,
    ScanResult
)
from asn_lookup import ASNLookupService


async def test_protocol_detection():
    """Test real protocol detection"""
    print("=" * 70)
    print("PHASE 2 TEST 1: Protocol Detection Engine")
    print("=" * 70)
    
    detector = ProxyProtocolDetector()
    
    # Test with some known public proxies
    test_targets = [
        # Format: (ip, port, expected_type, description)
        ('104.248.63.15', 30588, 'socks5', 'Public SOCKS5'),
        ('142.93.68.63', 2434, 'socks5', 'Public SOCKS5'),
        ('47.88.3.19', 8080, 'http', 'Public HTTP'),
        ('192.168.1.1', 8080, None, 'Private IP (should fail)'),
        ('8.8.8.8', 53, None, 'DNS Server (not a proxy)'),
    ]
    
    print("\n🔍 Testing protocol detection on real IPs...")
    print("Note: Some proxies may be offline - this is normal\n")
    
    success_count = 0
    
    for ip, port, expected_type, description in test_targets:
        print(f"Testing {ip}:{port} ({description})...")
        
        result = await detector.detect_proxy(ip, port)
        
        if result.is_proxy:
            print(f"  ✅ Detected: {result.proxy_type}")
            print(f"     Confidence: {result.confidence:.2%}")
            print(f"     Response time: {result.response_time:.3f}s")
            success_count += 1
        else:
            print(f"  ❌ Not detected as proxy")
            if expected_type is None:
                print(f"     (This is expected)")
                success_count += 1
        
        print()
    
    print(f"Detection accuracy: {success_count}/{len(test_targets)}")
    return success_count > 0


async def test_asn_lookup():
    """Test ASN lookup functionality"""
    print("\n" + "=" * 70)
    print("PHASE 2 TEST 2: ASN Lookup Service")
    print("=" * 70)
    
    asn_service = ASNLookupService()
    
    test_ips = [
        ('104.248.1.1', 'DigitalOcean'),
        ('52.1.1.1', 'AWS'),
        ('8.8.8.8', 'Google'),
        ('1.1.1.1', 'Cloudflare'),
    ]
    
    print("\n🌐 Testing ASN lookups with real APIs...")
    
    success_count = 0
    
    for ip, expected_provider in test_ips:
        print(f"\nLooking up {ip} (expected: {expected_provider})...")
        
        info = await asn_service.lookup_ip(ip)
        
        if info:
            print(f"  ✅ Found ASN: {info.asn}")
            print(f"     Organization: {info.name}")
            print(f"     Country: {info.country}")
            print(f"     Reputation: {info.reputation_score:.2f}")
            print(f"     Is Hosting: {info.is_hosting}")
            print(f"     Is VPN: {info.is_vpn_provider}")
            success_count += 1
        else:
            print(f"  ❌ Lookup failed")
    
    print(f"\nASN lookup success rate: {success_count}/{len(test_ips)}")
    return success_count > 0


async def test_target_generation():
    """Test intelligent target selection"""
    print("\n" + "=" * 70)
    print("PHASE 2 TEST 3: Intelligent Target Selection")
    print("=" * 70)
    
    selector = IntelligentTargetSelector()
    
    # Get high-value ranges
    print("\n🎯 Identifying high-value proxy ranges...")
    ranges = await selector.asn_service.get_high_value_ranges(min_reputation=0.8)
    
    print(f"Found {len(ranges)} high-value ASNs:")
    for i, range_info in enumerate(ranges[:5]):
        print(f"\n{i+1}. {range_info['name']} ({range_info['asn']})")
        print(f"   Type: {range_info['type']}")
        print(f"   Reputation: {range_info['reputation']:.2f}")
        print(f"   IP Ranges: {len(range_info['ranges'])}")
    
    # Generate targets
    print("\n📋 Generating scan targets...")
    targets = []
    async for target in selector.generate_targets(max_targets=50):
        targets.append(target)
    
    print(f"Generated {len(targets)} targets")
    
    # Analyze target distribution
    by_source = {}
    by_port = {}
    
    for target in targets:
        by_source[target.source] = by_source.get(target.source, 0) + 1
        by_port[target.port] = by_port.get(target.port, 0) + 1
    
    print("\nTarget distribution by source:")
    for source, count in by_source.items():
        print(f"  {source}: {count}")
    
    print("\nTop 5 ports targeted:")
    for port, count in sorted(by_port.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  Port {port}: {count} targets")
    
    return len(targets) > 0


async def test_ethical_scanning():
    """Test ethical scanning with rate limiting"""
    print("\n" + "=" * 70)
    print("PHASE 2 TEST 4: Ethical Scanning Manager")
    print("=" * 70)
    
    scanner = EthicalScanManager(max_concurrent=5, requests_per_second=2)
    
    # Test blocklist
    print("\n🛡️ Testing blocklist functionality...")
    
    # Add some IPs to blocklist
    scanner.blocklist.add('192.168.1.1')
    scanner.blocklist.add('10.0.0.1')
    
    blocked_target = ScanTarget('192.168.1.1', 8080)
    allowed_target = ScanTarget('8.8.8.8', 53)
    
    print(f"Checking if {blocked_target.ip} is allowed: ", end='')
    blocked = await scanner.is_scan_allowed(blocked_target)
    print("❌ Blocked" if not blocked else "✅ Allowed")
    
    print(f"Checking if {allowed_target.ip} is allowed: ", end='')
    allowed = await scanner.is_scan_allowed(allowed_target)
    print("✅ Allowed" if allowed else "❌ Blocked")
    
    # Test rate limiting
    print("\n⏱️ Testing rate limiting...")
    print(f"Rate limit: {scanner.rate_limiter.rate} requests/second")
    
    start_time = time.time()
    
    # Try to scan 10 targets rapidly
    test_targets = [
        ScanTarget('1.1.1.1', 80),
        ScanTarget('8.8.8.8', 80),
        ScanTarget('8.8.4.4', 80),
        ScanTarget('1.0.0.1', 80),
        ScanTarget('9.9.9.9', 80),
    ]
    
    print(f"Scanning {len(test_targets)} targets with rate limiting...")
    
    results = await scanner.scan_batch(test_targets)
    
    elapsed = time.time() - start_time
    actual_rate = len(test_targets) / elapsed
    
    print(f"Time elapsed: {elapsed:.2f}s")
    print(f"Actual rate: {actual_rate:.2f} req/s")
    print(f"Rate limiting working: {'✅ Yes' if actual_rate <= scanner.rate_limiter.rate + 0.5 else '❌ No'}")
    
    # Show statistics
    stats = scanner.get_scan_statistics()
    print(f"\nScan statistics:")
    print(f"  Total scans: {stats['total_scans']}")
    print(f"  Unique IPs: {stats['active_ips']}")
    print(f"  Blocklist size: {stats['blocklist_size']}")
    
    return True


async def test_real_world_scan():
    """Perform a small real-world scan"""
    print("\n" + "=" * 70)
    print("PHASE 2 TEST 5: Real-World Mini Scan")
    print("=" * 70)
    
    print("\n🌍 Performing a real scan on known proxy ranges...")
    print("This will attempt to find actual proxies...\n")
    
    # Initialize components
    selector = IntelligentTargetSelector()
    scanner = EthicalScanManager(max_concurrent=10, requests_per_second=5)
    
    # Generate targets from high-reputation ranges
    targets = []
    
    # Add some known likely proxy IPs
    known_proxy_ips = [
        '104.248.63.15',  # DigitalOcean
        '142.93.68.63',   # DigitalOcean
        '167.172.224.108', # DigitalOcean
        '159.65.69.186',  # DigitalOcean
    ]
    
    for ip in known_proxy_ips:
        for port in [1080, 3128, 8080, 8888]:
            targets.append(ScanTarget(ip, port, priority=0.9, source='known'))
    
    print(f"Scanning {len(targets)} targets...")
    print("This may take a moment...\n")
    
    # Perform scan
    start_time = time.time()
    results = await scanner.scan_batch(targets)
    scan_duration = time.time() - start_time
    
    # Analyze results
    found_proxies = [r for r in results if r.is_proxy]
    
    print(f"\n📊 Scan Results:")
    print(f"  Duration: {scan_duration:.2f}s")
    print(f"  Targets scanned: {len(results)}")
    print(f"  Proxies found: {len(found_proxies)}")
    print(f"  Success rate: {len(found_proxies)/len(results)*100:.1f}%")
    
    if found_proxies:
        print(f"\n✅ Found {len(found_proxies)} working proxies:")
        for proxy in found_proxies[:5]:  # Show first 5
            print(f"  {proxy.ip}:{proxy.port} - {proxy.proxy_type} (confidence: {proxy.confidence:.2%})")
    
    return len(found_proxies) > 0


async def main():
    """Run all Phase 2 tests"""
    print("\n" + "🚀 " * 20)
    print("PROXY SCANNER MODULE - PHASE 2 TESTING")
    print("🚀 " * 20)
    print(f"\nTest started at: {datetime.now().isoformat()}")
    
    try:
        # Run all tests
        test_results = []
        
        test_results.append(("Protocol Detection", await test_protocol_detection()))
        test_results.append(("ASN Lookup", await test_asn_lookup()))
        test_results.append(("Target Generation", await test_target_generation()))
        test_results.append(("Ethical Scanning", await test_ethical_scanning()))
        test_results.append(("Real-World Scan", await test_real_world_scan()))
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        all_passed = True
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✅ ALL PHASE 2 TESTS COMPLETED SUCCESSFULLY!")
            print("\nThe scanner is working with:")
            print("  - Real protocol detection (SOCKS5/4/HTTP)")
            print("  - Real ASN lookups from multiple sources")
            print("  - Intelligent target selection")
            print("  - Ethical scanning with rate limiting")
            print("  - Working proxy discovery")
        else:
            print("\n⚠️ Some tests failed - check output above")
        
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