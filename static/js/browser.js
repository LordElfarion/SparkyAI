/* Browser Functionality JavaScript */

// WebSocket connection for browser
let browserWs = null;
let browserWsConnected = false;

// Connect to Browser WebSocket
function connectBrowserWebSocket() {
    if (!sessionId) return;
    
    // Close existing connection if any
    if (browserWs) {
        browserWs.close();
    }
    
    // Create new connection
    browserWs = new WebSocket(`ws://${window.location.host}/ws/browser?session_id=${sessionId}`);
    
    // Connection opened
    browserWs.addEventListener('open', (event) => {
        console.log('Browser WebSocket connected');
        browserWsConnected = true;
    });
    
    // Connection closed
    browserWs.addEventListener('close', (event) => {
        console.log('Browser WebSocket disconnected');
        browserWsConnected = false;
        
        // Try to reconnect after a delay
        setTimeout(() => {
            connectBrowserWebSocket();
        }, 3000);
    });
    
    // Message received
    browserWs.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            handleBrowserWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing Browser WebSocket message:', error);
        }
    });
}

// Handle Browser WebSocket messages
function handleBrowserWebSocketMessage(data) {
    switch (data.type) {
        case 'connected':
            console.log('Browser WebSocket connected to session:', data.session_id);
            break;
            
        case 'screenshot':
            addScreenshot(data.data);
            break;
            
        case 'browser_notification':
            console.log('Browser notification:', data.content);
            break;
            
        default:
            console.log('Unknown Browser WebSocket message type:', data.type);
    }
}

// Initialize browser functionality
document.addEventListener('DOMContentLoaded', () => {
    // Connect WebSocket when session is ready
    const checkInterval = setInterval(() => {
        if (sessionId) {
            connectBrowserWebSocket();
            clearInterval(checkInterval);
        }
    }, 100);
    
    // Set up refresh button
    const refreshButton = document.getElementById('refresh-preview');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            // Request new screenshot if browser is active
            if (browserWsConnected) {
                browserWs.send(JSON.stringify({
                    action: 'screenshot'
                }));
            }
        });
    }
});