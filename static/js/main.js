// Theme Management
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.themeToggle = document.getElementById('themeToggle');
        this.themeIcon = document.getElementById('themeIcon');
        
        this.init();
    }
    
    init() {
        this.setTheme(this.theme);
        this.bindEvents();
    }
    
    bindEvents() {
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
    
    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (this.themeIcon) {
            if (theme === 'dark') {
                this.themeIcon.className = 'fas fa-sun';
            } else {
                this.themeIcon.className = 'fas fa-moon';
            }
        }
    }
    
    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        // Add a subtle animation
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
}

// Notification System
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            this.remove(notification);
        }, duration);
        
        return notification;
    }
    
    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.pointerEvents = 'auto';
        
        const icon = this.getIcon(type);
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <span>${message}</span>
                <button class="btn btn-sm ms-2 p-0" onclick="notificationManager.remove(this.parentElement.parentElement)" style="color: inherit; background: none; border: none;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        return notification;
    }
    
    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    remove(notification) {
        if (notification && notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }
}

// Loading Manager
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loadingOverlay');
        this.isLoading = false;
    }
    
    show(message = 'Processing...') {
        if (this.overlay) {
            const messageElement = this.overlay.querySelector('p');
            if (messageElement) {
                messageElement.textContent = message;
            }
            
            this.overlay.classList.add('show');
            this.isLoading = true;
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }
    }
    
    hide() {
        if (this.overlay) {
            this.overlay.classList.remove('show');
            this.isLoading = false;
            
            // Restore body scroll
            document.body.style.overflow = '';
        }
    }
}

// Form Validation Utilities
class FormValidator {
    static validateUrl(url) {
        try {
            const urlObj = new URL(url);
            const supportedDomains = [
                'instagram.com', 'www.instagram.com',
                'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com',
                'facebook.com', 'www.facebook.com', 'fb.watch',
                'twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'
            ];
            
            return supportedDomains.some(domain => 
                urlObj.hostname.toLowerCase().includes(domain)
            );
        } catch (e) {
            return false;
        }
    }
    
    static detectPlatform(url) {
        try {
            const urlObj = new URL(url);
            const hostname = urlObj.hostname.toLowerCase();
            
            if (hostname.includes('instagram.com')) return 'instagram';
            if (hostname.includes('tiktok.com')) return 'tiktok';
            if (hostname.includes('facebook.com') || hostname.includes('fb.watch')) return 'facebook';
            if (hostname.includes('twitter.com') || hostname.includes('x.com')) return 'twitter';
            
            return null;
        } catch (e) {
            return null;
        }
    }
}

// Animation Utilities
class AnimationManager {
    static fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    static fadeOut(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(element.style.opacity) || 1;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = startOpacity * (1 - progress);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    static slideIn(element, direction = 'up', duration = 300) {
        const transforms = {
            up: 'translateY(30px)',
            down: 'translateY(-30px)',
            left: 'translateX(30px)',
            right: 'translateX(-30px)'
        };
        
        element.style.transform = transforms[direction];
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOut = 1 - Math.pow(1 - progress, 3);
            
            element.style.opacity = easeOut;
            element.style.transform = `scale(${0.95 + 0.05 * easeOut}) ${transforms[direction].replace('30px', `${30 * (1 - easeOut)}px`)}`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.transform = '';
            }
        };
        
        requestAnimationFrame(animate);
    }
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, seconds] of Object.entries(intervals)) {
        const interval = Math.floor(diffInSeconds / seconds);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }
    
    return 'Just now';
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        } catch (err) {
            document.body.removeChild(textArea);
            return Promise.reject(err);
        }
    }
}

// Global instances
let themeManager;
let notificationManager;
let loadingManager;

// Global functions for convenience
function showNotification(message, type = 'info', duration = 5000) {
    return notificationManager.show(message, type, duration);
}

function showLoading(message = 'Processing...') {
    loadingManager.show(message);
}

function hideLoading() {
    loadingManager.hide();
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    themeManager = new ThemeManager();
    notificationManager = new NotificationManager();
    loadingManager = new LoadingManager();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading state to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitButton.disabled = true;
                
                // Re-enable after 30 seconds as fallback
                setTimeout(() => {
                    if (submitButton.disabled) {
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                }, 30000);
            }
        });
    });
    
    // Add auto-resize to textareas
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Add click-to-copy functionality
    document.querySelectorAll('[data-copy]').forEach(element => {
        element.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy') || this.textContent;
            copyToClipboard(textToCopy).then(() => {
                showNotification('Copied to clipboard!', 'success', 2000);
            }).catch(() => {
                showNotification('Failed to copy to clipboard', 'error', 3000);
            });
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search/URL input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const urlInput = document.getElementById('urlInput');
            if (urlInput) {
                urlInput.focus();
            }
        }
        
        // Escape to close modals/overlays
        if (e.key === 'Escape') {
            if (loadingManager.isLoading) {
                // Don't allow escape during loading
                return;
            }
            
            // Close any open modals
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
    
    console.log('Social Media Downloader initialized successfully');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Page became visible, could refresh data here
        console.log('Page is now visible');
    } else {
        // Page became hidden
        console.log('Page is now hidden');
    }
});

// Handle online/offline status
window.addEventListener('online', function() {
    showNotification('Connection restored', 'success', 3000);
});

window.addEventListener('offline', function() {
    showNotification('No internet connection', 'warning', 5000);
});

// Expose utilities globally for easy access
window.SocialMediaDownloader = {
    ThemeManager,
    NotificationManager,
    LoadingManager,
    FormValidator,
    AnimationManager,
    formatFileSize,
    formatTimeAgo,
    copyToClipboard,
    showNotification,
    showLoading,
    hideLoading
};
