// Main application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('SparkyAI app initialized');
    
    // Global variables
    window.sessionId = null;
    window.messageCount = 0;

    // DOM elements
    const appContainer = document.querySelector('.app-container');
    const chatsList = document.getElementById('chats-list');
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const newChatButton = document.getElementById('new-chat-btn');
    const tabButtons = document.querySelectorAll('.tab-button');
    const panelTabs = document.querySelectorAll('.panel-tab');
    const thinkingContainer = document.getElementById('thinking-container');
    const codeDisplay = document.getElementById('code-display');
    const previewContainer = document.getElementById('preview-container');
    const fileUploadButton = document.getElementById('file-upload-btn');
    const fileUploadInput = document.getElementById('file-upload-input');

    // Initialize the application
    initApp();

    // Function to initialize the application
    function initApp() {
        console.log('Initializing app...');
        
        // Set up event listeners
        setupEventListeners();
        
        // Try to load existing session
        const savedSessionId = localStorage.getItem('currentSessionId');
        
        if (savedSessionId) {
            try {
                // Verify session is valid
                fetch(`/api/sessions/info/${savedSessionId}`)
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            throw new Error('Session not found');
                        }
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            window.sessionId = savedSessionId;
                            loadChatHistory();
                        } else {
                            createNewSession();
                        }
                    })
                    .catch(error => {
                        console.error('Error checking session:', error);
                        createNewSession();
                    });
            } catch (error) {
                console.error('Error checking session:', error);
                createNewSession();
            }
        } else {
            createNewSession();
        }
        
        // Update connection status
        updateConnectionStatus();
    }

    // Set up event listeners
    function setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Send message on button click
        if (sendButton) {
            sendButton.addEventListener('click', function() {
                sendMessage();
            });
        }
        
        // Send message on Enter (but not with Shift+Enter)
        if (messageInput) {
            messageInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Auto-resize textarea as user types
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        }
        
        // Create new chat
        if (newChatButton) {
            newChatButton.addEventListener('click', function() {
                createNewSession();
            });
        }
        
        // Tab switching
        if (tabButtons) {
            tabButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const tabName = this.getAttribute('data-tab');
                    switchTab(tabName);
                });
            });
        }
        
        // Chat selection and deletion
        if (chatsList) {
            chatsList.addEventListener('click', function(e) {
                // Check if delete button was clicked
                if (e.target.classList.contains('delete-chat-btn')) {
                    const chatItem = e.target.closest('.chat-item');
                    if (chatItem) {
                        const chatId = chatItem.getAttribute('data-id');
                        deleteChat(chatId);
                        e.stopPropagation(); // Prevent chat selection
                    }
                } else {
                    // Chat item was clicked
                    const chatItem = e.target.closest('.chat-item');
                    if (chatItem) {
                        const chatId = chatItem.getAttribute('data-id');
                        if (chatId !== window.sessionId) {
                            switchToChat(chatId);
                        }
                    }
                }
            });
        }
        
        // File upload handling
        if (fileUploadButton && fileUploadInput) {
            fileUploadButton.addEventListener('click', function() {
                fileUploadInput.click();
            });
            
            fileUploadInput.addEventListener('change', function() {
                if (this.files.length > 0) {
                    handleFileUpload(this.files[0]);
                }
            });
        }
        
        // Handle drag and drop for file uploads
        const dropArea = document.querySelector('.file-drop-area');
        if (dropArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, function() {
                    dropArea.classList.add('dragover');
                }, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, function() {
                    dropArea.classList.remove('dragover');
                }, false);
            });
            
            dropArea.addEventListener('drop', function(e) {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileUpload(files[0]);
                }
            }, false);
        }
        
        // Connection status updates
        window.addEventListener('online', updateConnectionStatus);
        window.addEventListener('offline', updateConnectionStatus);
    }

    // Create a new chat session
    function createNewSession() {
        console.log('Creating new session...');
        
        fetch('/api/sessions/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: `Chat ${new Date().toLocaleString()}`
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.sessionId = data.session.id;
                localStorage.setItem('currentSessionId', window.sessionId);
                
                // Clear UI
                if (messagesContainer) {
                    messagesContainer.innerHTML = '';
                }
                
                if (thinkingContainer) {
                    thinkingContainer.innerHTML = '';
                }
                
                // Add welcome message
                addMessage('assistant', 'Hello! I am SparkyAI, your AI assistant. How can I help you today?');
                
                // Reset message count
                window.messageCount = 1;
                
                // Load chat list
                loadChatsList();
            } else {
                showError('Failed to create new session');
            }
        })
        .catch(error => {
            console.error('Error creating new session:', error);
            showError('Failed to create new session');
        });
    }

    // Send a message to the assistant
    function sendMessage() {
        if (!messageInput || !window.sessionId) return;
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to UI
        addMessage('user', message);
        
        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Show thinking indicator
        addThinkingIndicator();
        
        // Send to API
        fetch('/api/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: window.sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove thinking indicator
            removeThinkingIndicator();
            
            if (data.status === 'success') {
                // Add assistant response to UI
                addMessage('assistant', data.response);
                
                // Update message count
                window.messageCount += 2; // User + Assistant
                
                // Update chat list if needed
                if (window.messageCount === 3) { // After first exchange
                    loadChatsList();
                }
            } else {
                showError('Failed to get response from assistant');
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            removeThinkingIndicator();
            showError('Error communicating with the server');
        });
    }

    // Add a message to the UI
    function addMessage(role, content) {
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        // Process markdown-like syntax
        let processedContent = content
            .replace(/```([\s\S]*?)```/g, (match, code) => `<pre><code>${escapeHtml(code)}</code></pre>`)
            .replace(/`([^`]+)`/g, (match, code) => `<code>${escapeHtml(code)}</code>`)
            .replace(/\n/g, '<br>');
        
        messageContent.innerHTML = processedContent;
        
        messageDiv.appendChild(messageContent);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Highlight code blocks if highlight.js is available
        if (window.hljs) {
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }

    // Add thinking indicator
    function addThinkingIndicator() {
        if (!messagesContainer) return;
        
        const indicatorDiv = document.createElement('div');
        indicatorDiv.classList.add('message', 'assistant', 'thinking-indicator');
        indicatorDiv.innerHTML = '<div class="message-content">Thinking</div>';
        messagesContainer.appendChild(indicatorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Remove thinking indicator
    function removeThinkingIndicator() {
        const indicator = document.querySelector('.thinking-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Show error message
    function showError(message) {
        if (!messagesContainer) return;
        
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('message', 'error');
        errorDiv.innerHTML = `<div class="message-content">${message}</div>`;
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Load chat history
    function loadChatHistory() {
        if (!window.sessionId || !messagesContainer) return;
        
        // Clear messages
        messagesContainer.innerHTML = '';
        
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'system');
        loadingDiv.textContent = 'Loading chat history...';
        messagesContainer.appendChild(loadingDiv);
        
        // Load history from conversation file
        fetch(`/workspace/${window.sessionId}/conversation.json`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load chat history');
                }
                return response.json();
            })
            .then(data => {
                // Remove loading indicator
                loadingDiv.remove();
                
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        if (message.role === 'user' || message.role === 'assistant') {
                            addMessage(message.role, message.content);
                        }
                    });
                    
                    window.messageCount = data.messages.length;
                } else {
                    // No messages, add welcome
                    addMessage('assistant', 'Hello! I am SparkyAI, your AI assistant. How can I help you today?');
                    window.messageCount = 1;
                }
                
                // Update chat list
                loadChatsList();
                
                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                loadingDiv.remove();
                
                // Show welcome message
                addMessage('assistant', 'Hello! I am SparkyAI, your AI assistant. How can I help you today?');
                window.messageCount = 1;
            });
    }

    // Load chats list
    function loadChatsList() {
        if (!chatsList) return;
        
        fetch('/api/sessions/list')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.sessions) {
                    // Clear list
                    chatsList.innerHTML = '';
                    
                    // Add each chat
                    data.sessions.forEach(session => {
                        const chatItem = document.createElement('div');
                        chatItem.classList.add('chat-item');
                        chatItem.setAttribute('data-id', session.id);
                        
                        if (session.id === window.sessionId) {
                            chatItem.classList.add('active');
                        }
                        
                        // Create chat item content
                        chatItem.innerHTML = `
                            <span class="chat-title">${session.name}</span>
                            <button class="delete-chat-btn" title="Delete chat">×</button>
                        `;
                        
                        chatsList.appendChild(chatItem);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading chats list:', error);
            });
    }

    // Switch to a different chat
    function switchToChat(chatId) {
        window.sessionId = chatId;
        localStorage.setItem('currentSessionId', chatId);
        
        // Update active chat in UI
        const chatItems = document.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            if (item.getAttribute('data-id') === chatId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Load chat history
        loadChatHistory();
    }

    // Delete a chat
    function deleteChat(chatId) {
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }
        
        fetch(`/api/sessions/delete/${chatId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // If we deleted the current chat
                if (chatId === window.sessionId) {
                    createNewSession();
                } else {
                    // Just refresh the list
                    loadChatsList();
                }
            } else {
                alert('Failed to delete chat');
            }
        })
        .catch(error => {
            console.error('Error deleting chat:', error);
            alert('Error deleting chat');
        });
    }

    // Handle file upload
    function handleFileUpload(file) {
        if (!file) return;
        
        // Show file upload status
        addMessage('system', `Uploading file: ${file.name}`);
        
        // Read file as text or base64 depending on type
        const reader = new FileReader();
        
        // Text files to read as text
        const textTypes = ['text/plain', 'text/html', 'text/css', 'text/javascript', 'application/json', 'application/xml'];
        
        if (textTypes.includes(file.type) || file.name.endsWith('.py') || file.name.endsWith('.js')) {
            reader.readAsText(file);
        } else {
            // Other files as base64
            reader.readAsDataURL(file);
        }
        
        reader.onload = function() {
            const fileContent = reader.result;
            
            // Use file analyzer tool
            fetch('/api/tools/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tool: 'file_analyzer',
                    input: JSON.stringify({
                        action: 'analyze',
                        file_data: typeof fileContent === 'string' ? fileContent : fileContent.split(',')[1],
                        file_name: file.name,
                        file_type: file.type
                    }),
                    session_id: window.sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    addMessage('assistant', data.result);
                } else {
                    showError('Failed to analyze file');
                }
            })
            .catch(error => {
                console.error('Error analyzing file:', error);
                showError('Error analyzing file');
            });
        };
        
        reader.onerror = function() {
            showError('Error reading file');
        };
    }

    // Switch tabs
    function switchTab(tabName) {
        // Update tab buttons
        tabButtons.forEach(button => {
            if (button.getAttribute('data-tab') === tabName) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
        
        // Update tab panels
        panelTabs.forEach(panel => {
            if (panel.id === `${tabName}-panel`) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }

    // Update connection status
    function updateConnectionStatus() {
        const isOnline = navigator.onLine;
        let statusElem = document.querySelector('.connection-indicator');
        
        if (!statusElem) {
            statusElem = document.createElement('div');
            statusElem.classList.add('connection-indicator');
            document.body.appendChild(statusElem);
        }
        
        if (isOnline) {
            statusElem.innerHTML = '<span class="status-dot connected"></span> Connected';
            statusElem.title = 'Connected to server';
        } else {
            statusElem.innerHTML = '<span class="status-dot disconnected"></span> Offline';
            statusElem.title = 'No internet connection';
        }
    }

    // Escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Make key functions available globally
    window.addMessage = addMessage;
    window.switchTab = switchTab;
    window.sendMessage = sendMessage;
    window.createNewSession = createNewSession;
    window.loadChatsList = loadChatsList;
    window.handleFileUpload = handleFileUpload;
});
