#!/usr/bin/env python3
import os
from pathlib import Path

def ensure_directory(directory_path):
    """Make sure a directory exists."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")

def fix_websocket_js(project_root):
    """Fix WebSocket client implementation."""
    print("\n===== Fixing WebSocket client implementation =====")
    
    # Ensure the directory exists
    js_dir = project_root / "static" / "js"
    ensure_directory(js_dir)
    
    # Create the improved WebSocket.js file
    file_path = js_dir / "websocket.js"
    
    # Simple WebSocket implementation
    content = """
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
"""
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"✅ Created/Updated {file_path}")

def create_chat_fix_js(project_root):
    """Create a simple chat fix script."""
    print("\n===== Creating Chat Fix script =====")
    
    # Ensure the directory exists
    js_dir = project_root / "static" / "js"
    ensure_directory(js_dir)
    
    # Create the chat fix file
    file_path = js_dir / "chatFix.js"
    
    content = """
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat fix script loaded');
    
    // Find chat elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages-container');
    
    if (!messageInput || !sendButton) {
        console.error('Chat elements not found');
        return;
    }
    
    // Create a more reliable send function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add message to UI immediately
        if (messagesContainer) {
            const messageEl = document.createElement('div');
            messageEl.className = 'message user-message';
            messageEl.innerHTML = `
                <div class="message-content">${message}</div>
                <div class="message-timestamp">${new Date().toLocaleTimeString()}</div>
            `;
            messagesContainer.appendChild(messageEl);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Send via WebSocket if available
        if (window.websocketManager) {
            window.websocketManager.sendMessage({
                type: 'chat',
                content: message,
                id: 'msg_' + Date.now(),
                timestamp: new Date().toISOString()
            });
        } else {
            console.error('WebSocketManager not available');
            alert('Cannot send message: Not connected to server');
        }
        
        // Clear input
        messageInput.value = '';
    }
    
    // Add click handler
    sendButton.addEventListener('click', function(e) {
        e.preventDefault();
        sendMessage();
    });
    
    // Add Enter key handler
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Add test function
    window.testSendMessage = function(text) {
        messageInput.value = text || 'Test message';
        sendMessage();
    };
});
"""
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"✅ Created/Updated {file_path}")

def update_index_html(project_root):
    """Update index.html to include the chat fix script."""
    print("\n===== Updating index.html =====")
    
    # Find index.html
    file_path = project_root / "templates" / "index.html"
    
    if not os.path.exists(file_path):
        print(f"❌ Could not find {file_path}")
        return
    
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check if our scripts are already included
    scripts_to_add = []
    
    if '<script src="/static/js/chatFix.js">' not in content:
        scripts_to_add.append('<script src="/static/js/chatFix.js"></script>')
    
    # Add the scripts before the closing body tag
    if scripts_to_add:
        modified_content = content.replace(
            '</body>',
            '    ' + '\n    '.join(scripts_to_add) + '\n</body>'
        )
        
        with open(file_path, 'w') as file:
            file.write(modified_content)
        
        print(f"✅ Updated {file_path} - Added scripts: {', '.join(scripts_to_add)}")
    else:
        print(f"ℹ️ No changes needed for {file_path}")

def main():
    print("===== WebSocket Fix Script =====")
    project_root = Path(".")  # Current directory
    
    fix_websocket_js(project_root)
    create_chat_fix_js(project_root)
    update_index_html(project_root)
    
    print("\n===== All fixes applied! =====")
    print("1. Restart your server: python app.py")
    print("2. Open your browser to http://localhost:8000")
    print("3. Check your browser console (F12) for connection status")

if __name__ == "__main__":
    main()