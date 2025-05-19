/**
 * AI Meeting Assistant Browser Extension
 * Content Script - Injects into meeting platform pages
 */

// Global state
let isConnected = false;
let audioContext = null;
let mediaStream = null;
let audioProcessor = null;
let websocket = null;
let platformType = 'unknown';
let meetingId = '';

// Detect which platform we're on
function detectPlatform() {
    const url = window.location.href;
    if (url.includes('meet.google.com')) {
        platformType = 'meet';
        meetingId = url.split('/').pop();
    } else if (url.includes('zoom.us')) {
        platformType = 'zoom';
        meetingId = url.split('/j/')[1]?.split('?')[0] || '';
    } else if (url.includes('teams.microsoft.com')) {
        platformType = 'teams';
        // Teams meeting ID extraction is more complex
        meetingId = url.split('/').pop();
    } else {
        platformType = 'unknown';
    }
    
    console.log(`AI Meeting Assistant: Detected platform ${platformType} with meeting ID ${meetingId}`);
}

// Initialize audio capture
async function initializeAudioCapture() {
    try {
        // Request audio from the browser
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            },
            video: false
        });
        
        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000 // 16kHz for optimal speech recognition
        });
        
        // Create source node
        const source = audioContext.createMediaStreamSource(mediaStream);
        
        // Create processor node for raw audio data
        const processorNode = audioContext.createScriptProcessor(4096, 1, 1);
        
        // Connect nodes
        source.connect(processorNode);
        processorNode.connect(audioContext.destination);
        
        // Process audio data
        processorNode.onaudioprocess = processAudio;
        
        audioProcessor = processorNode;
        console.log('AI Meeting Assistant: Audio capture initialized');
        return true;
    } catch (error) {
        console.error('AI Meeting Assistant: Error initializing audio capture', error);
        return false;
    }
}

// Process audio data
function processAudio(event) {
    if (!isConnected || !websocket || websocket.readyState !== WebSocket.OPEN) {
        return;
    }
    
    // Get audio data
    const inputData = event.inputBuffer.getChannelData(0);
    
    // Convert to 16-bit PCM
    const pcmData = convertFloatTo16BitPCM(inputData);
    
    // Send to server if connected
    websocket.send(pcmData);
}

// Convert float audio data to 16-bit PCM
function convertFloatTo16BitPCM(input) {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output.buffer;
}

// Initialize WebSocket connection to backend
function connectToBackend() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
    }
    
    const backendUrl = 'ws://localhost:8000/ws';
    websocket = new WebSocket(backendUrl);
    
    websocket.onopen = () => {
        console.log('AI Meeting Assistant: Connected to backend');
        isConnected = true;
        
        // Send platform info
        websocket.send(JSON.stringify({
            action: 'start_meeting',
            platform: platformType,
            meeting_id: meetingId
        }));
        
        // Update UI
        updateUI('connected');
    };
    
    websocket.onclose = () => {
        console.log('AI Meeting Assistant: Disconnected from backend');
        isConnected = false;
        updateUI('disconnected');
    };
    
    websocket.onerror = (error) => {
        console.error('AI Meeting Assistant: WebSocket error', error);
        isConnected = false;
        updateUI('error');
    };
    
    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'answer') {
                displayAnswer(data);
            }
        } catch (error) {
            console.error('AI Meeting Assistant: Error processing message', error);
        }
    };
}

// Display an answer in the UI
function displayAnswer(data) {
    // Check if our UI container exists
    let container = document.getElementById('ai-meeting-assistant-container');
    if (!container) {
        // Create container
        container = document.createElement('div');
        container.id = 'ai-meeting-assistant-container';
        container.className = 'ai-meeting-assistant-container';
        document.body.appendChild(container);
        
        // Add styles if not already added
        if (!document.getElementById('ai-meeting-assistant-styles')) {
            const style = document.createElement('style');
            style.id = 'ai-meeting-assistant-styles';
            style.textContent = `
                .ai-meeting-assistant-container {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 350px;
                    max-height: 500px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 10000;
                    overflow: hidden;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                
                .ai-meeting-assistant-header {
                    background-color: #4a6cf7;
                    color: white;
                    padding: 10px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .ai-meeting-assistant-title {
                    margin: 0;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                .ai-meeting-assistant-controls {
                    display: flex;
                    gap: 5px;
                }
                
                .ai-meeting-assistant-control {
                    cursor: pointer;
                    color: white;
                    opacity: 0.8;
                    transition: opacity 0.2s;
                }
                
                .ai-meeting-assistant-control:hover {
                    opacity: 1;
                }
                
                .ai-meeting-assistant-content {
                    padding: 10px;
                    max-height: 400px;
                    overflow-y: auto;
                }
                
                .ai-meeting-assistant-answer {
                    background-color: #f8f9fa;
                    border-left: 4px solid #4a6cf7;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 0 4px 4px 0;
                    animation: fadeIn 0.5s ease-in-out;
                }
                
                .ai-meeting-assistant-question {
                    font-weight: bold;
                    margin-bottom: 5px;
                    font-size: 13px;
                }
                
                .ai-meeting-assistant-answer-text {
                    margin-bottom: 5px;
                    font-size: 13px;
                }
                
                .ai-meeting-assistant-timestamp {
                    font-size: 11px;
                    color: #6c757d;
                    text-align: right;
                }
                
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Create header
        const header = document.createElement('div');
        header.className = 'ai-meeting-assistant-header';
        
        const title = document.createElement('h3');
        title.className = 'ai-meeting-assistant-title';
        title.textContent = 'AI Meeting Assistant';
        
        const controls = document.createElement('div');
        controls.className = 'ai-meeting-assistant-controls';
        
        const minimize = document.createElement('span');
        minimize.className = 'ai-meeting-assistant-control';
        minimize.textContent = '−';
        minimize.title = 'Minimize';
        minimize.onclick = toggleMinimize;
        
        const close = document.createElement('span');
        close.className = 'ai-meeting-assistant-control';
        close.textContent = '×';
        close.title = 'Close';
        close.onclick = () => {
            container.remove();
        };
        
        controls.appendChild(minimize);
        controls.appendChild(close);
        
        header.appendChild(title);
        header.appendChild(controls);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'ai-meeting-assistant-content';
        
        container.appendChild(header);
        container.appendChild(content);
    }
    
    // Create answer element
    const answerElement = document.createElement('div');
    answerElement.className = 'ai-meeting-assistant-answer';
    
    const question = document.createElement('div');
    question.className = 'ai-meeting-assistant-question';
    question.textContent = data.question;
    
    const answerText = document.createElement('div');
    answerText.className = 'ai-meeting-assistant-answer-text';
    answerText.textContent = data.answer;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'ai-meeting-assistant-timestamp';
    timestamp.textContent = formatTimestamp(data.timestamp);
    
    answerElement.appendChild(question);
    answerElement.appendChild(answerText);
    answerElement.appendChild(timestamp);
    
    // Add to container
    const content = container.querySelector('.ai-meeting-assistant-content');
    content.prepend(answerElement);
    
    // Keep only the most recent 5 answers
    const answers = content.querySelectorAll('.ai-meeting-assistant-answer');
    if (answers.length > 5) {
        for (let i = 5; i < answers.length; i++) {
            answers[i].remove();
        }
    }
}

// Format timestamp for display
function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return '';
    }
}

// Toggle minimize/maximize
function toggleMinimize() {
    const container = document.getElementById('ai-meeting-assistant-container');
    const content = container.querySelector('.ai-meeting-assistant-content');
    const minimizeBtn = container.querySelector('.ai-meeting-assistant-control');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        minimizeBtn.textContent = '−';
        minimizeBtn.title = 'Minimize';
    } else {
        content.style.display = 'none';
        minimizeBtn.textContent = '+';
        minimizeBtn.title = 'Maximize';
    }
}

// Update UI based on connection state
function updateUI(state) {
    // Implement UI updates based on connection state
    console.log(`AI Meeting Assistant: UI state updated to ${state}`);
}

// Initialize extension
async function initialize() {
    console.log('AI Meeting Assistant: Initializing');
    
    // Detect platform
    detectPlatform();
    
    // Add control button to meeting UI
    addControlButton();
    
    // Listen for messages from popup or background
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'connect') {
            if (!isConnected) {
                connectToBackend();
                initializeAudioCapture().then(success => {
                    sendResponse({ success });
                });
                return true; // Indicates async response
            }
        } else if (message.action === 'disconnect') {
            if (isConnected) {
                disconnectFromBackend();
                sendResponse({ success: true });
            }
        } else if (message.action === 'status') {
            sendResponse({
                connected: isConnected,
                platform: platformType,
                meeting_id: meetingId
            });
        }
    });
}

// Add control button to the meeting UI
function addControlButton() {
    // Implementation depends on the specific platform
    // This is a simplified version
    
    const button = document.createElement('button');
    button.textContent = 'AI Assistant';
    button.style.position = 'fixed';
    button.style.bottom = '20px';
    button.style.left = '20px';
    button.style.zIndex = '10000';
    button.style.padding = '8px 12px';
    button.style.backgroundColor = '#4a6cf7';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.cursor = 'pointer';
    
    button.onclick = () => {
        if (isConnected) {
            disconnectFromBackend();
        } else {
            connectToBackend();
            initializeAudioCapture();
        }
    };
    
    // Add to page after a delay to ensure meeting UI has loaded
    setTimeout(() => {
        document.body.appendChild(button);
    }, 3000);
}

// Disconnect from backend
function disconnectFromBackend() {
    if (websocket) {
        websocket.close();
    }
    
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    isConnected = false;
    updateUI('disconnected');
    console.log('AI Meeting Assistant: Disconnected from backend');
}

// Initialize when the page is fully loaded
if (document.readyState === 'complete') {
    initialize();
} else {
    window.addEventListener('load', initialize);
}
