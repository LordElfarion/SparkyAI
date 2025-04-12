document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing main.js');
    
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const panelTabs = document.querySelectorAll('.panel-tab');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            console.log('Switching to tab:', tabName);
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active panel
            panelTabs.forEach(tab => {
                tab.classList.remove('active');
                if (tab.id === `${tabName}-panel`) {
                    tab.classList.add('active');
                }
            });
        });
    });
    
    // Auto resize message input
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            messageInput.style.height = '50px';
            
            const newHeight = Math.min(messageInput.scrollHeight, 120);
            messageInput.style.height = `${newHeight}px`;
        });
        
        // Prevent enter key from submitting form
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('send-button').click();
            }
        });
    }
});
