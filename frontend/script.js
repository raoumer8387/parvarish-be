// API Configuration
const API_BASE_URL = 'http://localhost:8000';  // Update this to your FastAPI backend URL

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Handle Enter key (Shift+Enter for new line)
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    debugger;
    // Display user message
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Disable input while processing
    setInputState(false);
    
    // Show loading indicator
    const loadingId = addLoadingMessage();
    
    try {
        // Call the backend API
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: 'web-user'  // You can implement proper user management later
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoadingMessage(loadingId);
        
        // Display bot response
        addMessage(data.response || data.message || 'No response received', 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        
        // Remove loading indicator
        removeLoadingMessage(loadingId);
        
        // Display error message
        addErrorMessage('Sorry, I encountered an error. Please make sure the backend server is running and try again.');
    } finally {
        // Re-enable input
        setInputState(true);
        userInput.focus();
    }
});

// Add message to chat
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (sender === 'bot') {
        const header = document.createElement('strong');
        header.textContent = 'Parvarish AI:';
        contentDiv.appendChild(header);
        
        // Format the message text (preserve line breaks)
        const paragraphs = text.split('\n\n');
        paragraphs.forEach(para => {
            if (para.trim()) {
                const p = document.createElement('p');
                p.textContent = para.trim();
                contentDiv.appendChild(p);
            }
        });
    } else {
        contentDiv.textContent = text;
    }
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Add loading indicator
function addLoadingMessage() {
    const loadingDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message loading-message';
    
    loadingDiv.innerHTML = `
        <div class="message-content">
            <span>Thinking</span>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(loadingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return loadingId;
}

// Remove loading indicator
function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

// Add error message
function addErrorMessage(text) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = '⚠️ ' + text;
    
    chatContainer.appendChild(errorDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Set input state (enabled/disabled)
function setInputState(enabled) {
    userInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
});
