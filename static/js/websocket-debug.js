/**
 * WebSocket connection debugger
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('WebSocket debug script loaded');
    
    // Wait a few seconds to allow other scripts to initialize
    setTimeout(function() {
        console.log('Checking WebSocket connection status...');
        
        if (!window.websocketManager) {
            console.error('WebSocketManager not found! It may not be initialized.');
            addDebugMessage('WebSocketManager not initialized');
            return;
        }
        
        console.log('WebSocketManager exists:', window.websocketManager);
        
        if (!window.websocketManager.socket) {
            console.error('WebSocket connection object not found!');
            addDebugMessage('WebSocket connection object not found');
            return;
        }
        
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        const state = window.websocketManager.socket.readyState;
        console.log('WebSocket state:', states[state]);
        addDebugMessage(`WebSocket state: ${states[state]}`);
        
        if (state !== WebSocket.OPEN) {
            console.error('WebSocket not in OPEN state!');
            
            // Try to reconnect
            console.log('Attempting to reconnect WebSocket...');
            addDebugMessage('Attempting to reconnect...');
            
            if (typeof window.websocketManager.connect === 'function') {
                window.websocketManager.connect();
            } else {
                console.error('WebSocketManager.connect() function not found!');
                addDebugMessage('WebSocketManager.connect() function not found');
            }
        } else {
            console.log('WebSocket connection is open and ready');
            addDebugMessage('WebSocket connection is open and ready');
            
            // Try a test ping
            if (typeof window.websocketManager.sendMessage === 'function') {
                window.websocketManager.sendMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
                console.log('Sent test ping message');
                addDebugMessage('Sent test ping message');
            }
        }
    }, 3000);
    
    function addDebugMessage(message) {
        // Add debug message to UI
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            const debugElement = document.createElement('div');
            debugElement.className = 'message system-message';
            debugElement.innerHTML = `
                <div class="message-content"><strong>Debug:</strong> ${message}</div>
            `;
            messagesContainer.appendChild(debugElement);
        }
        
        // Also add to a debug panel if it exists
        let debugContainer = document.getElementById('debug-container');
        if (!debugContainer) {
            // Create debug container if it doesn't exist
            debugContainer = document.createElement('div');
            debugContainer.id = 'debug-container';
            debugContainer.style.position = 'fixed';
            debugContainer.style.bottom = '10px';
            debugContainer.style.left = '10px';
            debugContainer.style.backgroundColor = 'rgba(0,0,0,0.7)';
            debugContainer.style.color = 'white';
            debugContainer.style.padding = '10px';
            debugContainer.style.borderRadius = '5px';
            debugContainer.style.maxWidth = '400px';
            debugContainer.style.maxHeight = '200px';
            debugContainer.style.overflow = 'auto';
            debugContainer.style.zIndex = '1000';
            debugContainer.innerHTML = '<h4>WebSocket Debug</h4>';
            document.body.appendChild(debugContainer);
        }
        
        const debugElement = document.createElement('div');
        debugElement.innerHTML = `<div>${message}</div>`;
        debugContainer.appendChild(debugElement);
    }
    
    // Add a manual connect button
    const connectButton = document.createElement('button');
    connectButton.textContent = 'Connect WebSocket';
    connectButton.style.position = 'fixed';
    connectButton.style.top = '10px';
    connectButton.style.right = '10px';
    connectButton.style.zIndex = '1000';
    connectButton.onclick = function() {
        if (window.websocketManager && typeof window.websocketManager.connect === 'function') {
            console.log('Manual WebSocket connection attempt');
            addDebugMessage('Manual connection attempt');
            window.websocketManager.connect();
        } else {
            console.error('Cannot manually connect: WebSocketManager not found');
            addDebugMessage('Cannot manually connect: WebSocketManager not found');
        }
    };
    document.body.appendChild(connectButton);
});
