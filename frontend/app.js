/**
 * ShariahFolio - WebSocket Client and Chat Logic
 */

class ShariahFolioChat {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;

        // DOM Elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.themeToggle = document.getElementById('themeToggle');
        this.connectionStatus = document.getElementById('connectionStatus');

        // Initialize
        this.init();
    }

    init() {
        // Set up event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.newChatBtn.addEventListener('click', () => this.newConversation());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());

        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                this.newConversation();
            }
        });

        // Load theme preference
        this.loadTheme();

        // Connect to WebSocket
        this.connect();
    }

    connect() {
        this.updateConnectionStatus('connecting', 'Connecting...');

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', 'Connected');
                this.updateSendButton();

                // Hide status after 2 seconds
                setTimeout(() => {
                    this.connectionStatus.classList.remove('visible');
                }, 2000);
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateSendButton();
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error', 'Connection error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus('error', 'Failed to connect');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting', `Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.updateConnectionStatus('error', 'Connection failed. Please refresh.');
        }
    }

    updateConnectionStatus(status, text) {
        this.connectionStatus.className = `connection-status visible ${status}`;
        this.connectionStatus.querySelector('.status-text').textContent = text;
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.removeTypingIndicator();
                this.removeProgressIndicator();
                this.addMessage(data.content, data.sender || 'assistant');
                break;

            case 'typing':
                if (data.status) {
                    this.showTypingIndicator();
                } else {
                    this.removeTypingIndicator();
                }
                break;

            case 'progress':
                // Show progress message (training status, etc.)
                this.showProgressIndicator(data.content);
                break;

            case 'error':
                this.removeTypingIndicator();
                this.removeProgressIndicator();
                this.addMessage(`⚠️ ${data.content}`, 'assistant');
                break;

            case 'system':
                this.addSystemMessage(data.content);
                break;
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message || !this.isConnected) return;

        // Add user message to chat
        this.addMessage(message, 'user');

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'message',
            content: message
        }));

        // Clear input
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();
    }

    addMessage(content, sender) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;

        const avatarEl = document.createElement('div');
        avatarEl.className = 'message-avatar';
        avatarEl.textContent = sender === 'user' ? '👤' : '🕌';

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';

        // Render markdown for assistant messages
        if (sender === 'assistant') {
            contentEl.innerHTML = marked.parse(content);
        } else {
            contentEl.textContent = content;
        }

        messageEl.appendChild(avatarEl);
        messageEl.appendChild(contentEl);

        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }

    addSystemMessage(content) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant';

        const avatarEl = document.createElement('div');
        avatarEl.className = 'message-avatar';
        avatarEl.textContent = 'ℹ️';

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = content;

        messageEl.appendChild(avatarEl);
        messageEl.appendChild(contentEl);

        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        // Remove existing indicator if any
        this.removeTypingIndicator();

        const typingEl = document.createElement('div');
        typingEl.className = 'message assistant';
        typingEl.id = 'typingIndicator';

        const avatarEl = document.createElement('div');
        avatarEl.className = 'message-avatar';
        avatarEl.textContent = '🕌';

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        typingEl.appendChild(avatarEl);
        typingEl.appendChild(contentEl);

        this.chatMessages.appendChild(typingEl);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showProgressIndicator(message) {
        // Update existing or create new progress indicator
        let progressEl = document.getElementById('progressIndicator');

        if (!progressEl) {
            progressEl = document.createElement('div');
            progressEl.className = 'message assistant';
            progressEl.id = 'progressIndicator';

            const avatarEl = document.createElement('div');
            avatarEl.className = 'message-avatar';
            avatarEl.textContent = '⚙️';

            const contentEl = document.createElement('div');
            contentEl.className = 'message-content progress-content';

            progressEl.appendChild(avatarEl);
            progressEl.appendChild(contentEl);
            this.chatMessages.appendChild(progressEl);
        }

        const contentEl = progressEl.querySelector('.progress-content');
        contentEl.innerHTML = `
            <div class="progress-message">
                <span class="progress-spinner">⏳</span>
                <span class="progress-text">${message}</span>
            </div>
        `;

        this.scrollToBottom();
    }

    removeProgressIndicator() {
        const indicator = document.getElementById('progressIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    newConversation() {
        // Clear chat messages
        this.chatMessages.innerHTML = '';

        // Reset on server
        if (this.isConnected) {
            this.ws.send(JSON.stringify({ type: 'reset' }));
        }

        // Add welcome message
        this.addMessage(`# Welcome back to ShariahFolio! 🕌📈

Ready to build a new Shariah-compliant portfolio. Tell me:
1. How much would you like to invest?
2. Any specific stocks or risk preference?`, 'assistant');
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', theme);
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
    }

    updateSendButton() {
        const hasContent = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasContent || !this.isConnected;
    }

    scrollToBottom() {
        const container = document.getElementById('chatContainer');
        container.scrollTop = container.scrollHeight;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chat = new ShariahFolioChat();
});
