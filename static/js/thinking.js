/* Thinking Process JavaScript */

// WebSocket connection for thinking process
let thinkingWs = null;
let thinkingWsConnected = false;

// Connect to Thinking WebSocket
function connectThinkingWebSocket() {
    if (!sessionId) return;
    
    // Close existing connection if any
    if (thinkingWs) {
        thinkingWs.close();
    }
    
    // Create new connection
    thinkingWs = new WebSocket(`ws://${window.location.host}/ws/thinking?session_id=${sessionId}`);
    
    // Connection opened
    thinkingWs.addEventListener('open', (event) => {
        console.log('Thinking WebSocket connected');
        thinkingWsConnected = true;
    });
    
    // Connection closed
    thinkingWs.addEventListener('close', (event) => {
        console.log('Thinking WebSocket disconnected');
        thinkingWsConnected = false;
        
        // Try to reconnect after a delay
        setTimeout(() => {
            connectThinkingWebSocket();
        }, 3000);
    });
    
    // Message received
    thinkingWs.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            handleThinkingWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing Thinking WebSocket message:', error);
        }
    });
}

// Handle Thinking WebSocket messages
function handleThinkingWebSocketMessage(data) {
    switch (data.type) {
        case 'connected':
            console.log('Thinking WebSocket connected to session:', data.session_id);
            break;
            
        case 'thinking_update':
            addThinkingStep(data.step);
            break;
            
        case 'thinking_complete':
            console.log('Thinking process complete:', data);
            break;
            
        case 'ping':
            // Ignore ping messages
            break;
            
        default:
            console.log('Unknown Thinking WebSocket message type:', data.type);
    }
}

// Add thinking step to UI
function addThinkingStep(step) {
    // Create step element
    const stepDiv = document.createElement('div');
    stepDiv.classList.add('thinking-step', step.type);
    stepDiv.setAttribute('data-id', step.id);
    
    // Create header
    const header = document.createElement('div');
    header.classList.add('thinking-step-header');
    
    // Set header text based on type
    switch (step.type) {
        case 'thinking':
            header.textContent = 'Thinking';
            break;
        case 'action':
            header.textContent = 'Action';
            break;
        case 'result':
            header.textContent = 'Result';
            break;
        case 'conclusion':
            header.textContent = 'Conclusion';
            break;
        default:
            header.textContent = step.type;
    }
    
    // Create content
    const content = document.createElement('div');
    content.classList.add('thinking-step-content');
    content.textContent = step.content;
    
    // Add to step
    stepDiv.appendChild(header);
    stepDiv.appendChild(content);
    
    // Add to container
    thinkingContainer.appendChild(stepDiv);
    
    // Scroll to bottom
    thinkingContainer.scrollTop = thinkingContainer.scrollHeight;
}

// Initialize thinking process
document.addEventListener('DOMContentLoaded', () => {
    // Connect WebSocket when session is ready
    const checkInterval = setInterval(() => {
        if (sessionId) {
            connectThinkingWebSocket();
            clearInterval(checkInterval);
        }
    }, 100);
});