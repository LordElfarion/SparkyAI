/**
 * Connection monitor to handle WebSocket connection status
 */
class ConnectionMonitor {
    constructor(websocketManager) {
        this.websocketManager = websocketManager;
        this.lastPingTime = Date.now();
        this.connectionIndicator = document.getElementById('connection-status') || this.createConnectionIndicator();
        this.checkInterval = null;
        
        // Register for pong events
        websocketManager.addEventHandler('pong', () => this.handlePong());
        
        // Start checking connection
        this.startMonitoring();
    }
    
    createConnectionIndicator() {
        // Create a connection status indicator
        const indicator = document.createElement('div');
        indicator.id = 'connection-status';
        indicator.className = 'connection-indicator';
        indicator.innerHTML = `<span class="status-dot connected"></span> Connected`;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .connection-indicator {
                position: fixed;
                bottom: 10px;
                right: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 1000;
                display: flex;
                align-items: center;
            }
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .connected { background-color: #4CAF50; }
            .connecting { background-color: #FFC107; }
            .disconnected { background-color: #F44336; }
        `;
        document.head.appendChild(style);
        document.body.appendChild(indicator);
        return indicator;
    }
    
    startMonitoring() {
        // Check connection every 10 seconds
        this.checkInterval = setInterval(() => this.checkConnection(), 10000);
    }
    
    checkConnection() {
        const now = Date.now();
        const timeSinceLastPong = now - this.lastPingTime;
        
        // If we haven't received a pong in 30 seconds, consider the connection unhealthy
        if (timeSinceLastPong > 30000) {
            this.updateConnectionStatus('disconnected');
            
            // Try to reconnect if socket is closed
            if (!this.websocketManager.socket || this.websocketManager.socket.readyState !== WebSocket.OPEN) {
                this.websocketManager.connect();
            }
        } else if (timeSinceLastPong > 15000) {
            // Warning state
            this.updateConnectionStatus('connecting');
        }
    }
    
    handlePong() {
        this.lastPingTime = Date.now();
        this.updateConnectionStatus('connected');
    }
    
    updateConnectionStatus(status) {
        const dot = this.connectionIndicator.querySelector('.status-dot');
        dot.className = 'status-dot ' + status;
        
        let text = 'Connected';
        if (status === 'connecting') text = 'Connecting...';
        if (status === 'disconnected') text = 'Disconnected';
        
        this.connectionIndicator.innerHTML = `<span class="status-dot ${status}"></span> ${text}`;
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait for WebSocketManager to be initialized
    const initConnectionMonitor = setInterval(() => {
        if (window.websocketManager) {
            new ConnectionMonitor(window.websocketManager);
            clearInterval(initConnectionMonitor);
        }
    }, 100);
});
