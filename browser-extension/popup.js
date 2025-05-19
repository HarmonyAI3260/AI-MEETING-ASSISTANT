/**
 * AI Meeting Assistant Browser Extension
 * Popup Script
 */

// DOM elements
const connectButton = document.getElementById('connect-button');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const platformInput = document.getElementById('platform');
const meetingIdInput = document.getElementById('meeting-id');
const apiKeyInput = document.getElementById('api-key');
const backendUrlInput = document.getElementById('backend-url');
const saveSettingsButton = document.getElementById('save-settings');

// Application state
let isConnected = false;
let currentTabId = null;

// Initialize popup
function initializePopup() {
    // Load saved settings
    loadSettings();
    
    // Check current connection status
    getCurrentTab().then(tab => {
        currentTabId = tab.id;
        checkConnectionStatus(tab.id);
    });
    
    // Set up event listeners
    connectButton.addEventListener('click', toggleConnection);
    saveSettingsButton.addEventListener('click', saveSettings);
}

// Get the current active tab
async function getCurrentTab() {
    const queryOptions = { active: true, currentWindow: true };
    const tabs = await chrome.tabs.query(queryOptions);
    return tabs[0];
}

// Check connection status from content script
function checkConnectionStatus(tabId) {
    chrome.tabs.sendMessage(tabId, { action: 'status' }, (response) => {
        if (chrome.runtime.lastError) {
            // Content script probably not injected yet
            updateUI('unavailable');
            return;
        }
        
        if (response && response.connected) {
            isConnected = true;
            updateUI('connected');
            
            // Update meeting info
            if (response.platform) {
                platformInput.value = response.platform;
            }
            
            if (response.meeting_id) {
                meetingIdInput.value = response.meeting_id;
            }
        } else {
            isConnected = false;
            updateUI('disconnected');
        }
    });
}

// Toggle connection state
function toggleConnection() {
    if (!currentTabId) {
        return;
    }
    
    const action = isConnected ? 'disconnect' : 'connect';
    
    // Disable button during action
    connectButton.disabled = true;
    connectButton.textContent = isConnected ? 'Disconnecting...' : 'Connecting...';
    
    // Send message to content script
    chrome.tabs.sendMessage(currentTabId, { action }, (response) => {
        if (chrome.runtime.lastError) {
            console.error('Error communicating with content script:', chrome.runtime.lastError);
            alert('Error communicating with the meeting page. Please make sure you are on a supported meeting platform.');
            connectButton.disabled = false;
            connectButton.textContent = isConnected ? 'Disconnect' : 'Connect to Meeting';
            return;
        }
        
        if (response && response.success) {
            isConnected = !isConnected;
            updateUI(isConnected ? 'connected' : 'disconnected');
        } else {
            alert('Failed to ' + action + ' to meeting. Please try again.');
            connectButton.disabled = false;
            connectButton.textContent = isConnected ? 'Disconnect' : 'Connect to Meeting';
        }
    });
}

// Update UI based on connection state
function updateUI(state) {
    switch (state) {
        case 'connected':
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
            connectButton.textContent = 'Disconnect';
            connectButton.disabled = false;
            break;
            
        case 'disconnected':
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Disconnected';
            connectButton.textContent = 'Connect to Meeting';
            connectButton.disabled = false;
            break;
            
        case 'unavailable':
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Not available on this page';
            connectButton.textContent = 'Connect to Meeting';
            connectButton.disabled = true;
            break;
    }
}

// Save settings to chrome storage
function saveSettings() {
    const settings = {
        apiKey: apiKeyInput.value,
        backendUrl: backendUrlInput.value
    };
    
    chrome.storage.sync.set({ 'aiMeetingAssistantSettings': settings }, () => {
        // Provide feedback
        saveSettingsButton.textContent = 'Saved!';
        setTimeout(() => {
            saveSettingsButton.textContent = 'Save Settings';
        }, 2000);
        
        // Send updated settings to content script if connected
        if (isConnected && currentTabId) {
            chrome.tabs.sendMessage(currentTabId, { 
                action: 'updateSettings',
                settings
            });
        }
    });
}

// Load settings from chrome storage
function loadSettings() {
    chrome.storage.sync.get('aiMeetingAssistantSettings', (result) => {
        const settings = result.aiMeetingAssistantSettings;
        if (settings) {
            if (settings.apiKey) {
                apiKeyInput.value = settings.apiKey;
            }
            
            if (settings.backendUrl) {
                backendUrlInput.value = settings.backendUrl;
            }
        }
    });
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePopup);
