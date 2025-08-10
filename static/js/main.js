/**
 * YouTube Transcript Chat - Enhanced JavaScript Application
 * Professional UI with improved UX and error handling
 */

class YouTubeTranscriptChat {
    constructor() {
        this.transcriptLoaded = false;
        this.chatHistory = [];
        this.isExtracting = false;
        this.isAsking = false;
        this.currentVideoId = null;

        this.initializeEventListeners();
        this.initializeUI();

        console.log('🎥 YouTube Transcript Chat initialized');
    }

    initializeEventListeners() {
        // Extract transcript button
        document.getElementById('extractBtn').addEventListener('click', () => {
            this.extractTranscript();
        });

        // Ask question button
        document.getElementById('askBtn').addEventListener('click', () => {
            this.askQuestion();
        });

        // Clear chat button
        document.getElementById('clearChatBtn').addEventListener('click', () => {
            this.clearChat();
        });

        // Enter key handling for inputs
        document.getElementById('youtubeUrl').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isExtracting) {
                this.extractTranscript();
            }
        });

        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isAsking && !e.target.disabled) {
                this.askQuestion();
            }
        });

        // URL input validation
        document.getElementById('youtubeUrl').addEventListener('input', (e) => {
            this.validateURL(e.target.value);
        });

        // Suggestion clicks
        this.initializeSuggestions();

        // Auto-resize text inputs
        this.initializeAutoResize();
    }

    initializeUI() {
        // Add welcome animation
        this.animateHeroSection();

        // Initialize tooltips if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    initializeSuggestions() {
        // Add click handlers for suggestion items
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-item')) {
                const suggestion = e.target.textContent.replace(/['"]/g, '');
                const questionInput = document.getElementById('questionInput');

                if (!questionInput.disabled) {
                    questionInput.value = suggestion;
                    questionInput.focus();
                }
            }
        });
    }

    initializeAutoResize() {
        const questionInput = document.getElementById('questionInput');
        questionInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }

    animateHeroSection() {
        const heroContent = document.querySelector('.hero-content');
        if (heroContent) {
            heroContent.style.opacity = '0';
            heroContent.style.transform = 'translateY(30px)';

            setTimeout(() => {
                heroContent.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
                heroContent.style.opacity = '1';
                heroContent.style.transform = 'translateY(0)';
            }, 200);
        }
    }

    validateURL(url) {
        const urlInput = document.getElementById('youtubeUrl');
        const extractBtn = document.getElementById('extractBtn');

        if (!url.trim()) {
            this.resetURLValidation();
            return;
        }

        const youtubeRegex = /^(https?://)?(www\.)?(youtube\.com|youtu\.be)/;

        if (youtubeRegex.test(url)) {
            urlInput.classList.remove('is-invalid');
            urlInput.classList.add('is-valid');
            extractBtn.disabled = false;
        } else {
            urlInput.classList.remove('is-valid');
            urlInput.classList.add('is-invalid');
            extractBtn.disabled = true;
        }
    }

    resetURLValidation() {
        const urlInput = document.getElementById('youtubeUrl');
        const extractBtn = document.getElementById('extractBtn');

        urlInput.classList.remove('is-valid', 'is-invalid');
        extractBtn.disabled = false;
    }

    async extractTranscript() {
        if (this.isExtracting) return;

        const urlInput = document.getElementById('youtubeUrl');
        const extractBtn = document.getElementById('extractBtn');
        const extractSpinner = document.getElementById('extractSpinner');
        const urlError = document.getElementById('urlError');
        const extractSuccess = document.getElementById('extractSuccess');
        const transcriptDisplay = document.getElementById('transcriptDisplay');

        const url = urlInput.value.trim();

        // Reset previous states
        this.hideElement(urlError);
        this.hideElement(extractSuccess);

        if (!url) {
            this.showError(urlError, 'Please enter a YouTube URL');
            urlInput.focus();
            return;
        }

        // Validate YouTube URL format
        const youtubeRegex = /^(https?://)?(www\.)?(youtube\.com|youtu\.be)/;
        if (!youtubeRegex.test(url)) {
            this.showError(urlError, 'Please enter a valid YouTube URL (youtube.com or youtu.be)');
            urlInput.focus();
            return;
        }

        // Show loading state
        this.isExtracting = true;
        this.setLoadingState(extractBtn, extractSpinner, true, 'Extracting...');

        // Add loading animation to transcript area
        this.showLoadingInContainer(transcriptDisplay);

        try {
            const response = await fetch('/extract_transcript', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (data.success) {
                // Display transcript with animation
                this.displayTranscript(data.transcript, data.video_id);

                this.showSuccess(extractSuccess, `Transcript extracted successfully! ${data.length || 0} characters loaded.`);

                // Enable chat functionality
                this.transcriptLoaded = true;
                this.currentVideoId = data.video_id;
                this.enableChatInput();

                // Clear any previous chat
                this.clearChatMessages();

                // Scroll to transcript
                setTimeout(() => {
                    document.querySelector('.transcript-card').scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }, 500);

            } else {
                this.showError(urlError, data.error || 'Failed to extract transcript');
                this.showEmptyTranscript();
            }
        } catch (error) {
            this.showError(urlError, 'Network error. Please check your connection and try again.');
            this.showEmptyTranscript();
            console.error('Extract transcript error:', error);
        } finally {
            this.isExtracting = false;
            this.setLoadingState(extractBtn, extractSpinner, false, 'Extract Transcript');
        }
    }

    displayTranscript(transcript, videoId) {
        const transcriptDisplay = document.getElementById('transcriptDisplay');
        const wordCount = transcript.split(' ').length;

        // Update word count
        const wordCountElement = document.getElementById('wordCount');
        const transcriptStats = document.getElementById('transcriptStats');

        if (wordCountElement && transcriptStats) {
            wordCountElement.textContent = wordCount.toLocaleString();
            transcriptStats.classList.remove('d-none');
        }

        // Display transcript with fade-in animation
        transcriptDisplay.innerHTML = `
            <div class="transcript-text fade-in">${this.escapeHtml(transcript)}</div>
        `;

        // Scroll to top of transcript
        transcriptDisplay.scrollTop = 0;
    }

    showEmptyTranscript() {
        const transcriptDisplay = document.getElementById('transcriptDisplay');
        const transcriptStats = document.getElementById('transcriptStats');

        transcriptStats.classList.add('d-none');

        transcriptDisplay.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-content">
                    <i class="fas fa-closed-captioning empty-state-icon"></i>
                    <h5>No transcript loaded</h5>
                    <p class="text-muted">
                        Enter a YouTube URL above and click "Extract Transcript" to get started
                    </p>
                    <div class="empty-state-features">
                        <div class="feature-item">
                            <i class="fas fa-check text-success me-2"></i>
                            Works with auto-generated captions
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-check text-success me-2"></i>
                            Supports multiple languages
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-check text-success me-2"></i>
                            Real-time processing
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showLoadingInContainer(container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-content">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h5>Extracting transcript...</h5>
                    <p class="text-muted">This may take a few seconds</p>
                </div>
            </div>
        `;
    }

    async askQuestion() {
        if (this.isAsking) return;

        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');
        const askSpinner = document.getElementById('askSpinner');
        const chatError = document.getElementById('chatError');

        const question = questionInput.value.trim();

        // Reset previous states
        this.hideElement(chatError);

        if (!question) {
            this.showError(chatError, 'Please enter a question');
            questionInput.focus();
            return;
        }

        if (!this.transcriptLoaded) {
            this.showError(chatError, 'Please extract a transcript first');
            return;
        }

        // Add user message to chat
        this.addChatMessage('user', question);
        questionInput.value = '';
        questionInput.style.height = 'auto';

        // Show loading state
        this.isAsking = true;
        this.setLoadingState(askBtn, askSpinner, true, 'Thinking...');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/ask_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator();

            if (data.success) {
                // Add AI response to chat with delay for natural feel
                setTimeout(() => {
                    this.addChatMessage('ai', data.response);
                }, 500);
            } else {
                this.showError(chatError, data.error || 'Failed to get AI response');
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.showError(chatError, 'Network error. Please check your connection and try again.');
            console.error('Ask question error:', error);
        } finally {
            this.isAsking = false;
            this.setLoadingState(askBtn, askSpinner, false, 'Ask');
            questionInput.focus();
        }
    }

    addChatMessage(type, message) {
        const chatMessages = document.getElementById('chatMessages');
        const timestamp = new Date().toLocaleTimeString();

        // If this is the first message, clear the placeholder text
        if (this.chatHistory.length === 0) {
            chatMessages.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        // Add avatar for AI messages
        const avatar = type === 'ai' ? '<i class="fas fa-robot me-2"></i>' : '<i class="fas fa-user me-2"></i>';

        messageDiv.innerHTML = `
            <div class="message-content">
                ${type === 'ai' ? '<i class="fas fa-robot me-2 text-success"></i>' : ''}
                ${this.formatMessage(message)}
            </div>
            <div class="message-time">${timestamp}</div>
        `;

        chatMessages.appendChild(messageDiv);

        // Smooth scroll to bottom
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });

        // Store in history
        this.chatHistory.push({ type, message, timestamp });

        // Add entrance animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';

        requestAnimationFrame(() => {
            messageDiv.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
    }

    formatMessage(message) {
        // Basic markdown-like formatting
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/\`(.*?)\`/g, '<code>$1</code>');
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot me-2 text-success"></i>
                <span class="typing-animation">
                    <span></span>
                    <span></span>
                    <span></span>
                </span>
            </div>
        `;

        // Add typing animation CSS
        if (!document.querySelector('#typingAnimationCSS')) {
            const style = document.createElement('style');
            style.id = 'typingAnimationCSS';
            style.textContent = `
                .typing-animation {
                    display: inline-flex;
                    gap: 2px;
                }
                .typing-animation span {
                    width: 6px;
                    height: 6px;
                    background-color: #6b7280;
                    border-radius: 50%;
                    animation: typing 1.4s infinite ease-in-out;
                }
                .typing-animation span:nth-child(1) { animation-delay: -0.32s; }
                .typing-animation span:nth-child(2) { animation-delay: -0.16s; }
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');

        // Add fade-out animation
        chatMessages.style.transition = 'opacity 0.3s ease-out';
        chatMessages.style.opacity = '0';

        setTimeout(() => {
            chatMessages.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-content">
                        <i class="fas fa-comments empty-state-icon"></i>
                        <h5>Chat cleared!</h5>
                        <p class="text-muted">
                            Ask another question about the video content
                        </p>
                        <div class="empty-state-suggestions">
                            <div class="suggestion-item">
                                "What is this video about?"
                            </div>
                            <div class="suggestion-item">
                                "Summarize the key points"
                            </div>
                            <div class="suggestion-item">
                                "What are the main topics covered?"
                            </div>
                        </div>
                    </div>
                </div>
            `;

            chatMessages.style.opacity = '1';
            this.chatHistory = [];

            // Clear session on server
            fetch('/clear_session', { method: 'POST' });

            // Show success message
            this.showTemporaryMessage('Chat cleared successfully!', 'success');

        }, 300);
    }

    clearChatMessages() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-content">
                    <i class="fas fa-comments empty-state-icon"></i>
                    <h5>Ready to chat!</h5>
                    <p class="text-muted">
                        Ask questions about the video content below
                    </p>
                    <div class="empty-state-suggestions">
                        <div class="suggestion-item">
                            "What is this video about?"
                        </div>
                        <div class="suggestion-item">
                            "Summarize the key points"
                        </div>
                        <div class="suggestion-item">
                            "What are the main topics covered?"
                        </div>
                    </div>
                </div>
            </div>
        `;
        this.chatHistory = [];
    }

    enableChatInput() {
        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');

        questionInput.disabled = false;
        askBtn.disabled = false;
        questionInput.placeholder = 'Ask a question about the video...';

        // Add subtle glow effect
        questionInput.classList.add('chat-enabled');

        // Auto-focus with delay
        setTimeout(() => {
            questionInput.focus();
        }, 1000);
    }

    setLoadingState(button, spinner, isLoading, text = null) {
        const btnText = button.querySelector('.btn-text');

        if (isLoading) {
            button.disabled = true;
            button.classList.add('loading');
            if (text) btnText.textContent = text;
            spinner.classList.remove('d-none');
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            if (text) btnText.textContent = text;
            spinner.classList.add('d-none');
        }
    }

    showError(element, message) {
        element.querySelector('.error-text').textContent = message;
        element.classList.remove('d-none');

        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideElement(element);
        }, 10000);

        // Scroll to error
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showSuccess(element, message) {
        element.querySelector('.success-text').textContent = message;
        element.classList.remove('d-none');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideElement(element);
        }, 5000);
    }

    showTemporaryMessage(message, type = 'info') {
        // Create temporary toast message
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed`;
        toast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: var(--shadow-xl);
            animation: slideInRight 0.3s ease-out;
        `;
        toast.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            ${message}
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in forwards';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);

        // Add animation styles if not present
        if (!document.querySelector('#toastAnimationCSS')) {
            const style = document.createElement('style');
            style.id = 'toastAnimationCSS';
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    hideElement(element) {
        element.classList.add('d-none');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Utility methods
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showTemporaryMessage('Copied to clipboard!', 'success');
        });
    }

    downloadTranscript() {
        if (!this.transcriptLoaded) return;

        const transcript = document.querySelector('.transcript-text').textContent;
        const blob = new Blob([transcript], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `youtube-transcript-${this.currentVideoId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showTemporaryMessage('Transcript downloaded!', 'success');
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.transcriptChat = new YouTubeTranscriptChat();

    // Add global error handler
    window.addEventListener('error', (e) => {
        console.error('Global error:', e.error);
        // Could show user-friendly error message here
    });

    // Add service worker for offline support (optional)
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {
            // Silently fail if no service worker
        });
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeTranscriptChat;
}
