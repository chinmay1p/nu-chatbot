// --- Configuration ---
// 📌 IMPORTANT: Replace 'https://your-api-domain.com/ask' with the actual deployed URL
const API_ENDPOINT = 'https://nu-chatbot-qyrh.onrender.com'; 

// --- UI Construction ---
function createChatWidget() {
    // 1. Chat Container (the whole widget)
    const chatContainer = document.createElement('div');
    chatContainer.id = 'nirma-chatbot-container';
    chatContainer.innerHTML = `
        <div id="nirma-chatbot-header">NirmaUni Assistant 💬</div>
        <div id="nirma-chatbot-body">
            <div class="chat-message bot-message">Hello! I'm your Nirma University AI Assistant. How can I help you today?</div>
        </div>
        <div id="nirma-chatbot-footer">
            <input type="text" id="nirma-chat-input" placeholder="Ask a question about Nirma University...">
            <button id="nirma-send-button">Send</button>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // 2. Event Listener for Send Button
    document.getElementById('nirma-send-button').addEventListener('click', sendMessage);
    document.getElementById('nirma-chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// --- Chat Communication ---
function appendMessage(sender, text) {
    const chatBody = document.getElementById('nirma-chatbot-body');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    messageDiv.textContent = text;
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll to the bottom
}

async function sendMessage() {
    const inputField = document.getElementById('nirma-chat-input');
    const userText = inputField.value.trim();
    
    if (userText === '') return;

    appendMessage('user', userText);
    inputField.value = ''; // Clear input

    try {
        appendMessage('bot', 'Typing...'); // Placeholder while waiting for API

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // The API expects the key 'input' in the payload
            body: JSON.stringify({ input: userText }) 
        });

        const data = await response.json();
        
        // Remove 'Typing...' message
        const chatBody = document.getElementById('nirma-chatbot-body');
        if (chatBody.lastChild.textContent === 'Typing...') {
            chatBody.lastChild.remove(); 
        }

        // The API returns the answer in the 'response' key
        const botResponse = data.response || 'Sorry, I could not get a response from the AI.';
        appendMessage('bot', botResponse);

    } catch (error) {
        console.error('API Error:', error);
        // Remove 'Typing...' and append error message
        const chatBody = document.getElementById('nirma-chatbot-body');
        if (chatBody.lastChild && chatBody.lastChild.textContent === 'Typing...') chatBody.lastChild.remove();
        appendMessage('bot', 'An error occurred while connecting to the server. Check your API endpoint.');
    }
}

// --- Initialization ---
// Check if the DOM is fully loaded before trying to inject the widget
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createChatWidget);
} else {
    createChatWidget();
}
