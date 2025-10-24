/**
 * MOBILE UX ENHANCEMENTS
 * Production-grade JavaScript for mobile interactions
 * 
 * Features:
 * - Table scroll indicators
 * - Modal swipe-to-close
 * - Action button dropdowns
 * - Haptic feedback (iOS/Android)
 * - Performance monitoring
 */

(function() {
    'use strict';
    
    // ========================================================================
    // TABLE SCROLL INDICATORS
    // ========================================================================
    
    function initTableScrollIndicators() {
        const tables = document.querySelectorAll('.table-container, div[style*="overflow-x: auto"]');
        
        tables.forEach(container => {
            // Check if scrollable
            if (container.scrollWidth > container.clientWidth) {
                container.classList.add('has-scroll');
                
                // Remove indicator when scrolled
                container.addEventListener('scroll', function() {
                    if (this.scrollLeft > 10) {
                        this.classList.add('scrolled');
                    } else {
                        this.classList.remove('scrolled');
                    }
                });
            }
        });
    }
    
    // ========================================================================
    // MODAL SWIPE-TO-CLOSE
    // ========================================================================
    
    function initModalSwipeClose() {
        const modals = document.querySelectorAll('div[id$="Modal"]');
        
        modals.forEach(modal => {
            let startY = 0;
            let currentY = 0;
            let isDragging = false;
            
            const modalContent = modal.querySelector('div[style*="background: white"]');
            if (!modalContent) return;
            
            modalContent.addEventListener('touchstart', function(e) {
                startY = e.touches[0].clientY;
                isDragging = true;
            });
            
            modalContent.addEventListener('touchmove', function(e) {
                if (!isDragging) return;
                
                currentY = e.touches[0].clientY;
                const diff = currentY - startY;
                
                // Only allow downward swipe
                if (diff > 0) {
                    this.style.transform = `translateY(${diff}px)`;
                    this.style.transition = 'none';
                }
            });
            
            modalContent.addEventListener('touchend', function(e) {
                if (!isDragging) return;
                isDragging = false;
                
                const diff = currentY - startY;
                
                // Close if swiped down more than 100px
                if (diff > 100) {
                    const closeBtn = modal.querySelector('button[onclick*="close"]');
                    if (closeBtn) {
                        closeBtn.click();
                    }
                } else {
                    // Reset position
                    this.style.transform = '';
                    this.style.transition = 'transform 0.3s ease';
                }
            });
        });
    }
    
    // ========================================================================
    // ACTION BUTTON DROPDOWNS (Mobile)
    // ========================================================================
    
    function initActionButtonDropdowns() {
        if (window.innerWidth > 768) return; // Desktop only
        
        const actionGroups = document.querySelectorAll('table td > div[style*="display: flex"]');
        
        actionGroups.forEach(group => {
            const buttons = group.querySelectorAll('.btn-sm');
            if (buttons.length <= 1) return;
            
            // Create dropdown container
            const dropdown = document.createElement('div');
            dropdown.className = 'mobile-action-dropdown';
            dropdown.style.cssText = 'position: relative;';
            
            // Keep first button visible
            const primaryBtn = buttons[0].cloneNode(true);
            primaryBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleDropdown(dropdown);
            });
            
            // Create dropdown menu
            const menu = document.createElement('div');
            menu.className = 'mobile-action-menu';
            menu.style.cssText = `
                position: absolute;
                bottom: 100%;
                right: 0;
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                box-shadow: var(--shadow-lg);
                padding: 8px;
                display: none;
                z-index: 1000;
                min-width: 150px;
            `;
            
            // Add other buttons to menu
            for (let i = 1; i < buttons.length; i++) {
                const menuItem = buttons[i].cloneNode(true);
                menuItem.style.cssText = `
                    width: 100%;
                    justify-content: flex-start;
                    margin-bottom: 4px;
                `;
                menu.appendChild(menuItem);
            }
            
            dropdown.appendChild(primaryBtn);
            dropdown.appendChild(menu);
            
            // Replace original group
            group.replaceWith(dropdown);
        });
    }
    
    function toggleDropdown(dropdown) {
        const menu = dropdown.querySelector('.mobile-action-menu');
        const isOpen = menu.style.display === 'block';
        
        // Close all other dropdowns
        document.querySelectorAll('.mobile-action-menu').forEach(m => {
            m.style.display = 'none';
        });
        
        // Toggle this dropdown
        menu.style.display = isOpen ? 'none' : 'block';
        
        // Close on outside click
        if (!isOpen) {
            setTimeout(() => {
                document.addEventListener('click', function closeDropdown(e) {
                    if (!dropdown.contains(e.target)) {
                        menu.style.display = 'none';
                        document.removeEventListener('click', closeDropdown);
                    }
                });
            }, 0);
        }
    }
    
    // ========================================================================
    // HAPTIC FEEDBACK
    // ========================================================================
    
    function initHapticFeedback() {
        // Check if device supports haptic feedback
        if (!('vibrate' in navigator)) return;
        
        // Add haptic feedback to all buttons
        document.addEventListener('click', function(e) {
            const button = e.target.closest('button, .btn, a.btn');
            if (button) {
                // Light tap (10ms)
                navigator.vibrate(10);
            }
        }, true);
        
        // Add haptic feedback to form submissions
        document.addEventListener('submit', function(e) {
            // Medium tap (20ms)
            navigator.vibrate(20);
        }, true);
    }
    
    // ========================================================================
    // PERFORMANCE MONITORING
    // ========================================================================
    
    function initPerformanceMonitoring() {
        // Monitor layout shifts
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.hadRecentInput) continue;
                    
                    // Log significant layout shifts
                    if (entry.value > 0.1) {
                        console.warn('Layout shift detected:', entry.value);
                    }
                }
            });
            
            observer.observe({ entryTypes: ['layout-shift'] });
        }
        
        // Monitor long tasks
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    // Log tasks longer than 50ms
                    if (entry.duration > 50) {
                        console.warn('Long task detected:', entry.duration + 'ms');
                    }
                }
            });
            
            observer.observe({ entryTypes: ['longtask'] });
        }
    }
    
    // ========================================================================
    // BOTTOM NAV ACTIVE STATE
    // ========================================================================
    
    function updateBottomNavActiveState() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.mobile-bottom-nav .nav-item');
        
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && currentPath.includes(href)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    // ========================================================================
    // PULL-TO-REFRESH (Optional)
    // ========================================================================
    
    function initPullToRefresh() {
        if (window.innerWidth > 768) return; // Mobile only
        
        let startY = 0;
        let currentY = 0;
        let isPulling = false;
        
        const pageContent = document.querySelector('.page-content');
        if (!pageContent) return;
        
        pageContent.addEventListener('touchstart', function(e) {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        });
        
        pageContent.addEventListener('touchmove', function(e) {
            if (!isPulling) return;
            
            currentY = e.touches[0].clientY;
            const diff = currentY - startY;
            
            // Show pull indicator
            if (diff > 80) {
                // Trigger refresh
                console.log('Pull to refresh triggered');
                // Add your refresh logic here
            }
        });
        
        pageContent.addEventListener('touchend', function() {
            isPulling = false;
        });
    }
    
    // ========================================================================
    // KEYBOARD HANDLING
    // ========================================================================
    
    function initKeyboardHandling() {
        // Adjust viewport when keyboard appears
        if ('visualViewport' in window) {
            window.visualViewport.addEventListener('resize', function() {
                const keyboardHeight = window.innerHeight - window.visualViewport.height;
                
                if (keyboardHeight > 100) {
                    // Keyboard is visible
                    document.body.style.paddingBottom = keyboardHeight + 'px';
                } else {
                    // Keyboard is hidden
                    document.body.style.paddingBottom = '';
                }
            });
        }
    }
    
    // ========================================================================
    // SAFE AREA INSETS (iPhone notch)
    // ========================================================================
    
    function initSafeAreaInsets() {
        // Add CSS variables for safe area insets
        const root = document.documentElement;
        
        // Check if safe area insets are supported
        if (CSS.supports('padding-top: env(safe-area-inset-top)')) {
            root.style.setProperty('--safe-area-top', 'env(safe-area-inset-top)');
            root.style.setProperty('--safe-area-bottom', 'env(safe-area-inset-bottom)');
            root.style.setProperty('--safe-area-left', 'env(safe-area-inset-left)');
            root.style.setProperty('--safe-area-right', 'env(safe-area-inset-right)');
        }
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        // Initialize all features
        initTableScrollIndicators();
        initModalSwipeClose();
        initActionButtonDropdowns();
        initHapticFeedback();
        initPerformanceMonitoring();
        updateBottomNavActiveState();
        initPullToRefresh();
        initKeyboardHandling();
        initSafeAreaInsets();
        
        // Re-initialize on dynamic content changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    initTableScrollIndicators();
                    initModalSwipeClose();
                    initActionButtonDropdowns();
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('✅ Mobile UX enhancements initialized');
    }
    
    // Start initialization
    init();
    
})();
