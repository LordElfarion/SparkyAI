
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
