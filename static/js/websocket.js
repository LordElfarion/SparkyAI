
class WebSocketManager {
    constructor(sessionId) {
        this.sessionId = sessionId || 'session_' + Date.now();
        this.socket = null;
        this.eventHandlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        console.log('WebSocketManager initialized');
        
        // Connect immediately
        this.connect();
        
        // Setup ping interval
        setInterval(() => {
            if (this.isConnected()) {
                this.sendMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
            }
        }, 30000);
    }
    
    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
    
    connect() {
        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
        console.log('Connecting to WebSocket:', wsUrl);
        
        try {
            // Close existing connection
            if (this.socket) {
                this.socket.close();
            }
            
            // Create new connection
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connection established!');
                this.reconnectAttempts = 0;
                this.updateStatus('Connected');
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Received message:', data.type);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket connection closed');
                this.updateStatus('Disconnected');
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Error');
            };
        } catch (e) {
            console.error('Error creating WebSocket:', e);
            this.attemptReconnect();
        }
    }
    
    updateStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = 'connection-status ' + status.toLowerCase();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            this.updateStatus('Failed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(30000, Math.pow(2, this.reconnectAttempts) * 1000);
        
        console.log(`Reconnecting in ${delay/1000} seconds (attempt ${this.reconnectAttempts})`);
        this.updateStatus('Reconnecting...');
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    handleMessage(data) {
        const type = data.type;
        
        // Call appropriate event handlers
        if (this.eventHandlers[type]) {
            this.eventHandlers[type].forEach(handler => {
                try {
                    handler(data);
                } catch (e) {
                    console.error(`Error in handler for ${type}:`, e);
                }
            });
        }
        
        // Default handling for common message types
        if (type === 'chat_message') {
            this.displayMessage(data.message);
        } else if (type === 'thinking_update') {
            this.updateThinking(data.step);
        }
    }
    
    displayMessage(message) {
        if (!message) return;
        
        const container = document.getElementById('messages-container');
        if (!container) return;
        
        const div = document.createElement('div');
        div.className = `message ${message.role}-message`;
        div.innerHTML = `
            <div class="message-content">${message.content}</div>
            <div class="message-timestamp">${new Date(message.timestamp).toLocaleTimeString()}</div>
        `;
        
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
    
    updateThinking(step) {
        if (!step) return;
        
        const container = document.getElementById('thinking-container');
        if (!container) return;
        
        const div = document.createElement('div');
        div.className = `thinking-step ${step.type || ''}`;
        div.textContent = step.content;
        
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
    
    sendMessage(data) {
        if (!this.isConnected()) {
            console.error('Cannot send message: WebSocket not connected');
            return false;
        }
        
        try {
            this.socket.send(JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Error sending message:', e);
            return false;
        }
    }
    
    addEventHandler(type, handler) {
        if (!this.eventHandlers[type]) {
            this.eventHandlers[type] = [];
        }
        this.eventHandlers[type].push(handler);
    }
    
    removeEventHandler(type, handler) {
        if (this.eventHandlers[type]) {
            this.eventHandlers[type] = this.eventHandlers[type].filter(h => h !== handler);
        }
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get or create session ID
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now();
        localStorage.setItem('session_id', sessionId);
    }
    
    // Create websocket manager
    window.websocketManager = new WebSocketManager(sessionId);
    
    // Setup chat form
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    
    if (messageInput && sendButton) {
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Send message
            window.websocketManager.sendMessage({
                type: 'chat',
                content: message,
                id: 'msg_' + Date.now(),
                timestamp: new Date().toISOString()
            });
            
            // Clear input
            messageInput.value = '';
        });
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });
    }
    
    // Add connection status indicator
    let statusElement = document.getElementById('connection-status');
    if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.id = 'connection-status';
        statusElement.className = 'connection-status connecting';
        statusElement.textContent = 'Connecting...';
        document.body.appendChild(statusElement);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .connection-status {
                position: fixed;
                bottom: 10px;
                right: 10px;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                color: white;
                background: #333;
                z-index: 9999;
            }
            .connected { background: #4CAF50; }
            .disconnected, .failed { background: #F44336; }
            .connecting { background: #2196F3; }
            .error { background: #FF9800; }
        `;
        document.head.appendChild(style);
    }
});
