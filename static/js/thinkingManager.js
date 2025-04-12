class ThinkingManager {
    constructor(containerId, wsManager) {
        this.container = document.getElementById(containerId);
        this.wsManager = wsManager;
        this.steps = [];
        this.initialize();
    }
    
    initialize() {
        console.log('Initializing ThinkingManager');
        
        // Register WebSocket event handlers
        this.wsManager.addEventListener('thinking_update', (data) => {
            console.log('Received thinking update:', data);
            this.addStep(data.step);
        });
        
        this.wsManager.addEventListener('thinking_complete', (data) => {
            console.log('Thinking complete:', data);
            this.markComplete(data);
        });
        
        // Load existing thinking steps if available
        this.loadThinkingSteps();
    }
    
    loadThinkingSteps() {
        const sessionId = localStorage.getItem('currentSessionId');
        if (!sessionId) return;
        
        fetch(`/api/thinking/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Loaded thinking steps:', data);
                this.steps = data.steps || [];
                this.render();
            })
            .catch(error => {
                console.error('Error loading thinking steps:', error);
            });
    }
    
    addStep(step) {
        this.steps.push(step);
        this.render();
    }
    
    markComplete(data) {
        // Add a visual indicator that thinking is complete
        const completionElement = document.createElement('div');
        completionElement.className = 'thinking-completion';
        completionElement.innerHTML = `
            <div class="completion-icon">✅</div>
            <div class="completion-text">Thinking complete (${Math.round(data.duration)} seconds)</div>
        `;
        this.container.appendChild(completionElement);
    }
    
    render() {
        // Clear the container
        this.container.innerHTML = '';
        
        // Create timeline element
        const timeline = document.createElement('div');
        timeline.className = 'thinking-timeline';
        
        // Add steps to timeline
        this.steps.forEach((step, index) => {
            const stepElement = this.createStepElement(step, index);
            timeline.appendChild(stepElement);
        });
        
        this.container.appendChild(timeline);
        
        // Scroll to bottom
        this.container.scrollTop = this.container.scrollHeight;
    }
    
    createStepElement(step, index) {
        const stepElement = document.createElement('div');
        stepElement.className = `thinking-step thinking-step-${step.type}`;
        stepElement.dataset.stepId = step.id;
        
        const timeStr = new Date(step.timestamp * 1000).toLocaleTimeString();
        
        // Create step content based on type
        let contentHtml = '';
        
        switch (step.type) {
            case 'thinking':
                contentHtml = `<div class="step-content">${step.content}</div>`;
                break;
                
            case 'action':
                contentHtml = `
                    <div class="step-content">
                        <div class="action-title">🛠️ Action: ${step.content}</div>
                        ${step.data.code ? `<pre><code class="language-${step.data.language || 'javascript'}">${step.data.code}</code></pre>` : ''}
                    </div>
                `;
                break;
                
            case 'result':
                contentHtml = `
                    <div class="step-content">
                        <div class="result-title">📊 Result:</div>
                        <div class="result-content">${step.content}</div>
                    </div>
                `;
                break;
                
            case 'conclusion':
                contentHtml = `
                    <div class="step-content">
                        <div class="conclusion-title">🎯 Conclusion:</div>
                        <div class="conclusion-content">${step.content}</div>
                    </div>
                `;
                break;
        }
        
        stepElement.innerHTML = `
            <div class="step-header">
                <span class="step-number">${index + 1}</span>
                <span class="step-time">${timeStr}</span>
            </div>
            ${contentHtml}
        `;
        
        // Apply syntax highlighting to code blocks
        if (step.type === 'action' && step.data.code) {
            setTimeout(() => {
                const codeBlock = stepElement.querySelector('code');
                if (codeBlock) {
                    hljs.highlightElement(codeBlock);
                }
            }, 0);
        }
        
        return stepElement;
    }
    
    clearThinking() {
        this.steps = [];
        this.render();
    }
}

// Initialize Thinking Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Setting up ThinkingManager');
    if (window.wsManager) {
        window.thinkingManager = new ThinkingManager('thinking-panel', window.wsManager);
    } else {
        // Wait for WebSocket to be initialized
        const checkWsManager = setInterval(() => {
            if (window.wsManager) {
                window.thinkingManager = new ThinkingManager('thinking-panel', window.wsManager);
                clearInterval(checkWsManager);
            }
        }, 100);
    }
});
