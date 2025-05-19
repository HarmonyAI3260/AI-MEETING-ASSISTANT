/**
 * Meeting Service
 * Manages the connection to meeting platforms and handles answer display
 */

class MeetingService {
    constructor() {
        this.currentPlatform = null;
        this.isConnected = false;
        this.answers = [];
        this.maxAnswers = 5; // Default number of answers to display
        this.displayMode = 'floating'; // Default display mode
        
        // Elements references
        this.answersList = document.getElementById('answers-list');
        this.floatingWindow = null;
    }

    /**
     * Initialize the meeting service
     */
    initialize() {
        // Set up WebSocket message handlers
        websocketManager.on('answer', (data) => this.handleAnswer(data));
        
        // Load settings
        this.loadSettings();
        
        // Set up UI event listeners
        this.setupEventListeners();
        
        console.log('Meeting service initialized');
    }

    /**
     * Set up UI event listeners
     */
    setupEventListeners() {
        // Platform buttons
        const platformButtons = document.querySelectorAll('.platform-btn');
        platformButtons.forEach(button => {
            button.addEventListener('click', () => {
                platformButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.currentPlatform = button.getAttribute('data-platform');
            });
        });
        
        // Connect button
        const connectBtn = document.getElementById('connect-btn');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.toggleConnection());
        }
        
        // Settings modal
        const settingsLink = document.getElementById('settings-link');
        const settingsModal = document.getElementById('settings-modal');
        const closeBtn = document.querySelector('.close-btn');
        const saveSettingsBtn = document.getElementById('save-settings');
        
        if (settingsLink && settingsModal) {
            settingsLink.addEventListener('click', (e) => {
                e.preventDefault();
                settingsModal.style.display = 'block';
            });
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                settingsModal.style.display = 'none';
            });
        }
        
        // Click outside modal to close
        window.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                settingsModal.style.display = 'none';
            }
        });
        
        // Save settings
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        }
    }

    /**
     * Toggle connection to meeting platform
     */
    async toggleConnection() {
        if (this.isConnected) {
            // Disconnect
            await this.disconnectFromMeeting();
        } else {
            // Connect
            await this.connectToMeeting();
        }
    }

    /**
     * Connect to a meeting platform
     */
    async connectToMeeting() {
        if (!this.currentPlatform) {
            alert('Please select a meeting platform');
            return;
        }
        
        const connectBtn = document.getElementById('connect-btn');
        const meetingId = document.getElementById('meeting-id').value;
        
        // Update UI
        if (connectBtn) {
            connectBtn.textContent = 'Connecting...';
            connectBtn.disabled = true;
        }
        
        try {
            // Connect to WebSocket
            await websocketManager.connect();
            
            // Send connection request
            websocketManager.send({
                action: 'start_meeting',
                platform: this.currentPlatform,
                meeting_id: meetingId
            });
            
            // Update UI
            this.isConnected = true;
            if (connectBtn) {
                connectBtn.textContent = 'Disconnect';
                connectBtn.disabled = false;
            }
            
            // Show floating window if that's the display mode
            if (this.displayMode === 'floating') {
                this.createFloatingWindow();
            }
            
            console.log(`Connected to ${this.currentPlatform} meeting`);
        } catch (error) {
            console.error('Connection error:', error);
            alert('Failed to connect. Please try again.');
            
            // Reset UI
            if (connectBtn) {
                connectBtn.textContent = 'Connect';
                connectBtn.disabled = false;
            }
        }
    }

    /**
     * Disconnect from the current meeting
     */
    async disconnectFromMeeting() {
        const connectBtn = document.getElementById('connect-btn');
        
        // Update UI
        if (connectBtn) {
            connectBtn.textContent = 'Disconnecting...';
            connectBtn.disabled = true;
        }
        
        try {
            // Send disconnect request
            if (websocketManager.isConnected) {
                websocketManager.send({
                    action: 'stop_meeting'
                });
                
                // Disconnect WebSocket
                websocketManager.disconnect();
            }
            
            // Update UI
            this.isConnected = false;
            if (connectBtn) {
                connectBtn.textContent = 'Connect';
                connectBtn.disabled = false;
            }
            
            // Remove floating window if it exists
            if (this.floatingWindow) {
                document.body.removeChild(this.floatingWindow);
                this.floatingWindow = null;
            }
            
            console.log('Disconnected from meeting');
        } catch (error) {
            console.error('Disconnection error:', error);
            
            // Reset UI
            if (connectBtn) {
                connectBtn.textContent = 'Disconnect';
                connectBtn.disabled = false;
            }
        }
    }

    /**
     * Handle incoming answer from the backend
     * @param {Object} data - Answer data
     */
    handleAnswer(data) {
        if (!data.question || !data.answer) {
            console.warn('Received invalid answer data', data);
            return;
        }
        
        // Add to answers list
        this.answers.unshift({
            question: data.question,
            answer: data.answer,
            timestamp: data.timestamp || new Date().toISOString()
        });
        
        // Limit the number of answers to display
        if (this.maxAnswers > 0 && this.answers.length > this.maxAnswers) {
            this.answers = this.answers.slice(0, this.maxAnswers);
        }
        
        // Update UI
        this.renderAnswers();
    }

    /**
     * Render answers in the UI
     */
    renderAnswers() {
        // Determine where to render (main list or floating window)
        const targetElement = this.displayMode === 'floating' && this.floatingWindow 
            ? this.floatingWindow.querySelector('.floating-content') 
            : this.answersList;
            
        if (!targetElement) {
            console.warn('Target element for answers not found');
            return;
        }
        
        // Clear any empty state message
        if (this.answers.length > 0) {
            targetElement.innerHTML = '';
        }
        
        // Render each answer
        this.answers.forEach(answer => {
            const answerCard = document.createElement('div');
            answerCard.className = 'answer-card';
            
            const formattedTime = this.formatTimestamp(answer.timestamp);
            
            answerCard.innerHTML = `
                <div class="answer-question">${answer.question}</div>
                <div class="answer-text">${answer.answer}</div>
                <div class="answer-timestamp">${formattedTime}</div>
            `;
            
            targetElement.appendChild(answerCard);
        });
    }

    /**
     * Create a floating window for displaying answers
     */
    createFloatingWindow() {
        // Remove existing window if any
        if (this.floatingWindow) {
            document.body.removeChild(this.floatingWindow);
        }
        
        // Create window
        this.floatingWindow = document.createElement('div');
        this.floatingWindow.className = 'floating-window';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'floating-header';
        
        const title = document.createElement('h3');
        title.className = 'floating-title';
        title.textContent = 'AI Meeting Assistant';
        
        const minimize = document.createElement('span');
        minimize.className = 'floating-minimize';
        minimize.textContent = '−';
        minimize.title = 'Minimize';
        
        header.appendChild(title);
        header.appendChild(minimize);
        
        // Create content area
        const content = document.createElement('div');
        content.className = 'floating-content';
        
        if (this.answers.length === 0) {
            content.innerHTML = '<div class="empty-state"><p>Questions detected during the meeting will appear here.</p></div>';
        }
        
        // Add to window
        this.floatingWindow.appendChild(header);
        this.floatingWindow.appendChild(content);
        
        // Add to body
        document.body.appendChild(this.floatingWindow);
        
        // Minimize functionality
        minimize.addEventListener('click', () => {
            if (content.style.display === 'none') {
                content.style.display = 'block';
                minimize.textContent = '−';
                minimize.title = 'Minimize';
            } else {
                content.style.display = 'none';
                minimize.textContent = '+';
                minimize.title = 'Expand';
            }
        });
        
        // Render existing answers
        this.renderAnswers();
    }

    /**
     * Format timestamp for display
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time
     */
    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '';
        }
    }

    /**
     * Save user settings
     */
    saveSettings() {
        const apiKeyInput = document.getElementById('api-key');
        const displayModeInputs = document.querySelectorAll('input[name="display-mode"]');
        const maxAnswersSelect = document.getElementById('max-answers');
        
        // Get values
        const apiKey = apiKeyInput ? apiKeyInput.value : '';
        let displayMode = this.displayMode;
        displayModeInputs.forEach(input => {
            if (input.checked) {
                displayMode = input.value;
            }
        });
        const maxAnswers = maxAnswersSelect ? parseInt(maxAnswersSelect.value, 10) : 5;
        
        // Save settings
        const settings = {
            apiKey,
            displayMode,
            maxAnswers
        };
        localStorage.setItem('meetingAssistantSettings', JSON.stringify(settings));
        
        // Apply settings
        this.displayMode = displayMode;
        this.maxAnswers = maxAnswers;
        
        // Send API key to backend if connected
        if (apiKey && websocketManager.isConnected) {
            websocketManager.send({
                action: 'update_settings',
                api_key: apiKey
            });
        }
        
        // Update UI
        if (this.displayMode === 'floating' && this.isConnected && !this.floatingWindow) {
            this.createFloatingWindow();
        } else if (this.displayMode !== 'floating' && this.floatingWindow) {
            document.body.removeChild(this.floatingWindow);
            this.floatingWindow = null;
            this.renderAnswers();
        }
        
        // Close modal
        const settingsModal = document.getElementById('settings-modal');
        if (settingsModal) {
            settingsModal.style.display = 'none';
        }
        
        alert('Settings saved successfully');
    }

    /**
     * Load user settings
     */
    loadSettings() {
        const settingsString = localStorage.getItem('meetingAssistantSettings');
        if (!settingsString) {
            return;
        }
        
        try {
            const settings = JSON.parse(settingsString);
            
            // Apply settings
            if (settings.displayMode) {
                this.displayMode = settings.displayMode;
                const displayModeInput = document.querySelector(`input[name="display-mode"][value="${settings.displayMode}"]`);
                if (displayModeInput) {
                    displayModeInput.checked = true;
                }
            }
            
            if (settings.maxAnswers !== undefined) {
                this.maxAnswers = settings.maxAnswers;
                const maxAnswersSelect = document.getElementById('max-answers');
                if (maxAnswersSelect) {
                    maxAnswersSelect.value = settings.maxAnswers;
                }
            }
            
            if (settings.apiKey) {
                const apiKeyInput = document.getElementById('api-key');
                if (apiKeyInput) {
                    apiKeyInput.value = settings.apiKey;
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
}

// Create global instance
const meetingService = new MeetingService();
