class BrowserManager {
    constructor(containerId, wsManager) {
        this.container = document.getElementById(containerId);
        this.wsManager = wsManager;
        this.screenshots = [];
        this.currentScreenshotIndex = -1;
        this.initialize();
    }
    
    initialize() {
        // Register WebSocket event handlers
        this.wsManager.addEventListener('browser_screenshot', (data) => {
            this.addScreenshot(data);
        });
        
        this.wsManager.addEventListener('browser_notification', (data) => {
            this.addNotification(data);
        });
        
        // Create viewer elements
        this.createViewerElements();
    }
    
    createViewerElements() {
        // Create screenshot viewer
        const viewerContainer = document.createElement('div');
        viewerContainer.className = 'browser-viewer-container';
        
        // Image display
        this.imageDisplay = document.createElement('div');
        this.imageDisplay.className = 'browser-image-display';
        this.imageDisplay.innerHTML = '<div class="no-screenshot">No screenshots available</div>';
        
        // Controls
        const controls = document.createElement('div');
        controls.className = 'browser-controls';
        
        // Navigation buttons
        const prevButton = document.createElement('button');
        prevButton.className = 'browser-control-btn';
        prevButton.textContent = 'â†';
        prevButton.addEventListener('click', () => this.showPreviousScreenshot());
        
        const nextButton = document.createElement('button');
        nextButton.className = 'browser-control-btn';
        nextButton.textContent = 'â†’';
        nextButton.addEventListener('click', () => this.showNextScreenshot());
        
        // Counter
        this.counter = document.createElement('div');
        this.counter.className = 'browser-counter';
        this.counter.textContent = '0/0';
        
        controls.appendChild(prevButton);
        controls.appendChild(this.counter);
        controls.appendChild(nextButton);
        
        // Notification area
        this.notificationArea = document.createElement('div');
        this.notificationArea.className = 'browser-notifications';
        
        // Assemble viewer
        viewerContainer.appendChild(this.imageDisplay);
        viewerContainer.appendChild(controls);
        viewerContainer.appendChild(this.notificationArea);
        
        this.container.appendChild(viewerContainer);
    }
    
    addScreenshot(data) {
        const screenshot = {
            id: this.screenshots.length,
            imageData: data.data,
            timestamp: data.timestamp
        };
        
        this.screenshots.push(screenshot);
        this.currentScreenshotIndex = this.screenshots.length - 1;
        this.showCurrentScreenshot();
    }
    
    showCurrentScreenshot() {
        if (this.currentScreenshotIndex >= 0 && this.currentScreenshotIndex < this.screenshots.length) {
            const screenshot = this.screenshots[this.currentScreenshotIndex];
            
            // Update image display
            this.imageDisplay.innerHTML = `
                <img src="data:image/png;base64,${screenshot.imageData}" alt="Browser Screenshot">
                <div class="screenshot-timestamp">${new Date(screenshot.timestamp).toLocaleTimeString()}</div>
            `;
            
            // Update counter
            this.counter.textContent = `${this.currentScreenshotIndex + 1}/${this.screenshots.length}`;
        } else {
            this.imageDisplay.innerHTML = '<div class="no-screenshot">No screenshots available</div>';
            this.counter.textContent = '0/0';
        }
    }
    
    showPreviousScreenshot() {
        if (this.currentScreenshotIndex > 0) {
            this.currentScreenshotIndex--;
            this.showCurrentScreenshot();
        }
    }
    
    showNextScreenshot() {
        if (this.currentScreenshotIndex < this.screenshots.length - 1) {
            this.currentScreenshotIndex++;
            this.showCurrentScreenshot();
        }
    }
    
    addNotification(data) {
        const notification = document.createElement('div');
        notification.className = 'browser-notification';
        
        const time = new Date(data.timestamp).toLocaleTimeString();
        notification.innerHTML = `
            <span class="notification-time">${time}</span>
            <span class="notification-message">${data.message}</span>
        `;
        
        this.notificationArea.appendChild(notification);
        
        // Auto-scroll to bottom
        this.notificationArea.scrollTop = this.notificationArea.scrollHeight;
        
        // Remove old notifications when there are too many
        const maxNotifications = 50;
        while (this.notificationArea.children.length > maxNotifications) {
            this.notificationArea.removeChild(this.notificationArea.firstChild);
        }
    }
    
    clearScreenshots() {
        this.screenshots = [];
        this.currentScreenshotIndex = -1;
        this.showCurrentScreenshot();
        this.notificationArea.innerHTML = '';
    }
}

// Initialize Browser Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.wsManager) {
        window.browserManager = new BrowserManager('preview-panel', window.wsManager);
    } else {
        // Wait for WebSocket to be initialized
        const checkWsManager = setInterval(() => {
            if (window.wsManager) {
                window.browserManager = new BrowserManager('preview-panel', window.wsManager);
                clearInterval(checkWsManager);
            }
        }, 100);
    }
});
