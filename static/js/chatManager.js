class ChatManager {
    constructor(messagesContainerId, inputId, sendButtonId, chatsListId, newChatBtnId, wsManager) {
        this.messagesContainer = document.getElementById(messagesContainerId);
        this.input = document.getElementById(inputId);
        this.sendButton = document.getElementById(sendButtonId);
        this.chatsList = document.getElementById(chatsListId);
        this.newChatBtn = document.getElementById(newChatBtnId);
        this.wsManager = wsManager;
        this.messages = [];
        this.sessions = [];
        this.currentSessionId = localStorage.getItem('currentSessionId');
        this.isProcessing = false;
        
        console.log('ChatManager initialized with session ID:', this.currentSessionId);
        this.initialize();
    }
    
    initialize() {
        console.log('Initializing ChatManager');
        
        // Register event handlers
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                console.log('Send button clicked');
                this.sendMessage();
            });
        } else {
            console.error('Send button not found');
        }
        
        if (this.input) {
            this.input.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendMessage();
                }
            });
        } else {
            console.error('Message input not found');
        }
        
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => {
                console.log('New chat button clicked');
                this.createNewChat();
            });
        } else {
            console.error('New chat button not found');
        }
        
        // Register WebSocket event handlers
        this.wsManager.addEventListener('chat_message', (data) => {
            console.log('Received chat message:', data);
            this.addMessage(data.message);
        });
        
        // Load chat sessions
        this.loadChatSessions();
        
        // Load current chat messages
        if (this.currentSessionId) {
            this.loadMessages(this.currentSessionId);
        }
    }
    
    loadChatSessions() {
        console.log('Loading chat sessions');
        fetch('/api/chat/list')
            .then(response => response.json())
            .then(data => {
                console.log('Chat sessions loaded:', data);
                this.sessions = data.sessions || [];
                this.renderChatList();
            })
            .catch(error => {
                console.error('Error loading chat sessions:', error);
            });
    }
    
    renderChatList() {
        console.log('Rendering chat list');
        // Clear the chat list
        if (!this.chatsList) {
            console.error('Chats list element not found');
            return;
        }
        
        this.chatsList.innerHTML = '';
        
        // Add chat items
        this.sessions.forEach(session => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            
            // Set active class if this is the current session
            if (session.id === this.currentSessionId) {
                chatItem.classList.add('active');
            }
            
            // Get first message or use placeholder
            const firstMessage = session.message_count > 0 ? 
                session.first_message || 'Chat' : 
                'New Chat';
            
            const date = new Date(session.created_at).toLocaleDateString();
            
            chatItem.innerHTML = `
                <div class="chat-item-content">
                    <div class="chat-title">${firstMessage}</div>
                    <div class="chat-date">${date}</div>
                </div>
                <div class="chat-actions">
                    <button class="delete-chat-btn" data-session-id="${session.id}">🗑️</button>
                </div>
            `;
            
            // Add click event to select chat
            chatItem.querySelector('.chat-item-content').addEventListener('click', () => {
                console.log('Chat selected:', session.id);
                this.selectChat(session.id);
            });
            
            // Add click event to delete button
            chatItem.querySelector('.delete-chat-btn').addEventListener('click', (event) => {
                event.stopPropagation();
                console.log('Delete chat clicked:', session.id);
                this.deleteChat(session.id);
            });
            
            this.chatsList.appendChild(chatItem);
        });
    }
    
    loadMessages(sessionId) {
        console.log('Loading messages for session:', sessionId);
        fetch(`/api/chat/${sessionId}/messages`)
            .then(response => response.json())
            .then(data => {
                console.log('Messages loaded:', data);
                this.messages = data.messages || [];
                this.renderMessages();
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
    }
    
    renderMessages() {
        console.log('Rendering messages, count:', this.messages.length);
        // Clear the messages container
        if (!this.messagesContainer) {
            console.error('Messages container not found');
            return;
        }
        
        this.messagesContainer.innerHTML = '';
        
        // Add messages
        this.messages.forEach(message => {
            this.renderMessage(message);
        });
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    renderMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message-container ${message.role}-message`;
        
        const avatar = message.role === 'user' ? 
            '/static/img/user-avatar.png' : 
            '/static/img/ai-avatar.png';
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <img src="${avatar}" alt="${message.role} Avatar">
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessageContent(message.content)}</div>
                <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
    }
    
    formatMessageContent(content) {
        // Convert Markdown-style formatting to HTML
        let formattedContent = content;
        
        // Replace code blocks
        formattedContent = formattedContent.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (_, language, code) => {
            return `<pre><code class="language-${language || 'plaintext'}">${this.escapeHtml(code)}</code></pre>`;
        });
        
        // Replace inline code
        formattedContent = formattedContent.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Replace bold text
        formattedContent = formattedContent.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Replace italic text
        formattedContent = formattedContent.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Replace line breaks
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        
        return formattedContent;
    }
    
    escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }
    
    sendMessage() {
        const message = this.input.value.trim();
        if (!message || this.isProcessing) {
            console.log('Message empty or already processing');
            return;
        }
        
        console.log('Sending message:', message);
        this.isProcessing = true;
        
        // Clear input
        this.input.value = '';
        
        // Add message to UI immediately
        const userMessage = {
            id: 'temp-' + Date.now(),
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        
        this.addMessage(userMessage);
        
        // Add thinking indicator
        this.addThinkingIndicator();
        
        // Send message to server
        fetch(`/api/chat/${this.currentSessionId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: message
            })
        })
        .then(response => response.json())
        .then(data => {
            // Message sent successfully
            console.log('Message sent, response:', data);
            
            // Update local message with server-generated ID
            userMessage.id = data.id;
        })
        .catch(error => {
            console.error('Error sending message:', error);
            
            // Remove thinking indicator
            this.removeThinkingIndicator();
            this.isProcessing = false;
        });
    }
    
    addMessage(message) {
        console.log('Adding message:', message);
        // Check if message already exists
        const existingIndex = this.messages.findIndex(m => m.id === message.id);
        
        if (existingIndex >= 0) {
            // Update existing message
            this.messages[existingIndex] = message;
            
            // Update in UI
            const messageElements = this.messagesContainer.querySelectorAll('.message-container');
            if (messageElements[existingIndex]) {
                messageElements[existingIndex].querySelector('.message-text').innerHTML = 
                    this.formatMessageContent(message.content);
            }
        } else {
            // Add new message
            this.messages.push(message);
            this.renderMessage(message);
        }
        
        // If this is an AI message, remove thinking indicator and update processing state
        if (message.role === 'assistant') {
            this.removeThinkingIndicator();
            this.isProcessing = false;
        }
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    addThinkingIndicator() {
        console.log('Adding thinking indicator');
        const indicatorElement = document.createElement('div');
        indicatorElement.className = 'message-container assistant-message thinking-indicator';
        
        indicatorElement.innerHTML = `
            <div class="message-avatar">
                <img src="/static/img/ai-avatar.png" alt="AI Avatar">
            </div>
            <div class="message-content">
                <div class="message-text">
                    <div class="thinking-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(indicatorElement);
        this.scrollToBottom();
    }
    
    removeThinkingIndicator() {
        console.log('Removing thinking indicator');
        const indicator = this.messagesContainer.querySelector('.thinking-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    createNewChat() {
        console.log('Creating new chat');
        fetch('/api/chat', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // Store new session ID
            this.currentSessionId = data.session_id;
            localStorage.setItem('currentSessionId', this.currentSessionId);
            console.log('Created new chat with session ID:', this.currentSessionId);
            
            // Clear messages
            this.messages = [];
            this.renderMessages();
            
            // Reload chat sessions
            this.loadChatSessions();
            
            // Reset processing state
            this.isProcessing = false;
            
            // Update WebSocket connection
            this.wsManager.disconnect();
            this.wsManager = new WebSocketManager(this.currentSessionId);
            this.wsManager.connect();
            
            // Clear thinking and code panels
            if (window.thinkingManager) window.thinkingManager.clearThinking();
            if (window.browserManager) window.browserManager.clearScreenshots();
        })
        .catch(error => {
            console.error('Error creating new chat:', error);
        });
    }
    
    selectChat(sessionId) {
        if (sessionId === this.currentSessionId) {
            console.log('Chat already selected:', sessionId);
            return;
        }
        
        console.log('Selecting chat:', sessionId);
        this.currentSessionId = sessionId;
        localStorage.setItem('currentSessionId', sessionId);
        
        // Update active state in chat list
        const chatItems = this.chatsList.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            item.classList.remove('active');
            const deleteBtn = item.querySelector('.delete-chat-btn');
            if (deleteBtn && deleteBtn.dataset.sessionId === sessionId) {
                item.classList.add('active');
            }
        });
        
        // Load messages for selected chat
        this.loadMessages(sessionId);
        
        // Update WebSocket connection
        this.wsManager.disconnect();
        this.wsManager = new WebSocketManager(sessionId);
        this.wsManager.connect();
        
        // Load thinking steps for this session
        if (window.thinkingManager) {
            window.thinkingManager.loadThinkingSteps();
        }
    }
    
    deleteChat(sessionId) {
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }
        
        console.log('Deleting chat:', sessionId);
        fetch(`/api/chat/${sessionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Chat deleted, response:', data);
            
            // Check if current chat was deleted
            if (sessionId === this.currentSessionId) {
                // Create a new chat
                this.createNewChat();
            } else {
                // Just reload chat list
                this.loadChatSessions();
            }
        })
        .catch(error => {
            console.error('Error deleting chat:', error);
        });
    }
}

// Initialize Chat Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Setting up ChatManager');
    if (window.wsManager) {
        window.chatManager = new ChatManager(
            'messages-container', 
            'message-input', 
            'send-button', 
            'chats-list', 
            'new-chat-btn', 
            window.wsManager
        );
    } else {
        // Wait for WebSocket to be initialized
        const checkWsManager = setInterval(() => {
            if (window.wsManager) {
                window.chatManager = new ChatManager(
                    'messages-container', 
                    'message-input', 
                    'send-button', 
                    'chats-list', 
                    'new-chat-btn', 
                    window.wsManager
                );
                clearInterval(checkWsManager);
            }
        }, 100);
    }
});
