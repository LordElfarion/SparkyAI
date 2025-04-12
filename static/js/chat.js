/* Chat Functionality JavaScript */

// WebSocket connection
let ws = null;
let wsConnected = false;
let reconnectAttempts = 0;
let reconnectTimer = null;

// Connect to WebSocket
function connectWebSocket() {
    if (!sessionId) return;
    
    // Close existing connection if any
    if (ws) {
        ws.close();
    }
    
    // Create new connection
    console.log('Connecting to WebSocket...');
    ws = new WebSocket(`ws://${window.location.host}/ws/chat?session_id=${sessionId}`);
    
    // Connection opened
    ws.addEventListener('open', (event) => {
        console.log('WebSocket connected');
        wsConnected = true;
        reconnectAttempts = 0;
        clearTimeout(reconnectTimer);
        
        // Update status indicator
        updateWebSocketStatus('connected');
    });
    
    // Connection closed
    ws.addEventListener('close', (event) => {
        console.log('WebSocket disconnected');
        wsConnected = false;
        
        // Update status indicator
        updateWebSocketStatus('disconnected');
        
        // Try to reconnect
        reconnectWebSocket();
    });
    
    // Connection error
    ws.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
        wsConnected = false;
        
        // Update status indicator
        updateWebSocketStatus('disconnected');
    });
    
    // Message received
    ws.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    });
}

// Reconnect WebSocket
function reconnectWebSocket() {
    // Max 5 reconnect attempts
    if (reconnectAttempts >= 5) {
        console.log('Max reconnect attempts reached');
        return;
    }
    
    reconnectAttempts++;
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    const delay = Math.pow(2, reconnectAttempts - 1) * 1000;
    
    console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${reconnectAttempts})`);
    
    // Update status indicator
    updateWebSocketStatus('connecting');
    
    // Set timer for reconnect
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
        connectWebSocket();
    }, delay);
}

// Update WebSocket status indicator
function updateWebSocketStatus(status) {
    const indicator = document.querySelector('.connection-indicator');
    if (!indicator) return;
    
    const dot = indicator.querySelector('.status-dot');
    
    // Remove all status classes
    dot.classList.remove('connected', 'connecting', 'disconnected');
    
    // Add appropriate class
    dot.classList.add(status);
    
    // Update title
    switch (status) {
        case 'connected':
            indicator.setAttribute('title', 'Connected to server');
            break;
        case 'connecting':
            indicator.setAttribute('title', 'Connecting...');
            break;
        case 'disconnected':
            indicator.setAttribute('title', 'Disconnected from server');
            break;
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'session_info':
            console.log('Session info:', data);
            break;
            
        case 'message_received':
            console.log('Message received:', data);
            break;
            
        case 'agent_response':
            // Add agent response to UI
            addMessage('assistant', data.message);
            break;
            
        case 'status':
            updateAgentStatus(data.status);
            break;
            
        case 'thinking_update':
            // Add thinking step to UI
            addThinkingStep(data.step);
            break;
            
        case 'screenshot':
            // Add screenshot to preview panel
            addScreenshot(data.data);
            break;
            
        case 'error':
            showError(data.message);
            break;
            
        default:
            console.log('Unknown WebSocket message type:', data.type);
    }
}

// Send message via WebSocket
function sendWebSocketMessage(message) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return false;
    }
    
    try {
        ws.send(JSON.stringify({
            message: message
        }));
        return true;
    } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
    }
}

// Update agent status
function updateAgentStatus(status) {
    // Remove existing status classes
    appContainer.classList.remove('status-thinking', 'status-processing', 'status-idle', 'status-error');
    
    // Add new status class
    appContainer.classList.add(`status-${status}`);
    
    // Update UI based on status
    switch (status) {
        case 'thinking':
            // If there's no thinking indicator, add one
            if (!document.querySelector('.thinking-indicator')) {
                addThinkingIndicator();
            }
            break;
            
        case 'idle':
            // Remove thinking indicator
            removeThinkingIndicator();
            break;
    }
}

// Add screenshot to preview panel
function addScreenshot(imageData) {
    // Activate preview panel
    switchTab('preview');
    
    // Clear existing content
    previewContainer.innerHTML = '';
    
    // Create image element
    const img = document.createElement('img');
    img.src = imageData;
    img.alt = 'Screenshot';
    img.classList.add('preview-image');
    
    // Add to container
    previewContainer.appendChild(img);
}

// Initialize chat functionality
document.addEventListener('DOMContentLoaded', () => {
    // Connect WebSocket when session is ready
    const checkInterval = setInterval(() => {
        if (sessionId) {
            connectWebSocket();
            clearInterval(checkInterval);
        }
    }, 100);
});