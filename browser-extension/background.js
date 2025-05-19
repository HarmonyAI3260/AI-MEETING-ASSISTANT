/**
 * AI Meeting Assistant Browser Extension
 * Background Script
 */

// Listen for installation or update
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Meeting Assistant extension installed or updated');
  
  // Set default settings if not already set
  chrome.storage.sync.get('aiMeetingAssistantSettings', (result) => {
    if (!result.aiMeetingAssistantSettings) {
      chrome.storage.sync.set({
        'aiMeetingAssistantSettings': {
          apiKey: '',
          backendUrl: 'http://localhost:8000'
        }
      });
    }
  });
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getStatus') {
    // This action can be used to check if the background script is running
    sendResponse({ status: 'running' });
  }
  
  // Always return true if we want to send a response asynchronously
  return true;
});

// Handle audio capture permissions (bypasses content script limitations)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureTab') {
    // Get active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (!activeTab) {
        sendResponse({ success: false, error: 'No active tab found' });
        return;
      }
      
      // Request tab audio capture
      chrome.tabCapture.capture({
        audio: true,
        video: false,
        audioConstraints: {
          mandatory: {
            chromeMediaSource: 'tab'
          }
        }
      }, (stream) => {
        if (chrome.runtime.lastError) {
          sendResponse({ 
            success: false, 
            error: chrome.runtime.lastError.message 
          });
          return;
        }
        
        if (!stream) {
          sendResponse({ 
            success: false, 
            error: 'Failed to capture tab audio' 
          });
          return;
        }
        
        // We can't directly pass the stream to content script
        // Instead, we create an audio context in the background script
        // and process the audio here, sending the processed data to content script
        
        sendResponse({ success: true, message: 'Audio capture started' });
      });
    });
    
    return true; // Required for async response
  }
});

// Listen for browser action clicks (toolbar icon)
chrome.action.onClicked.addListener((tab) => {
  // Only enable on meeting platforms
  const url = tab.url || '';
  const isMeetingPlatform = 
    url.includes('meet.google.com') ||
    url.includes('zoom.us') ||
    url.includes('teams.microsoft.com');
  
  if (!isMeetingPlatform) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: 'AI Meeting Assistant',
      message: 'This extension only works on supported meeting platforms: Google Meet, Zoom, and Microsoft Teams.',
      priority: 2
    });
    return;
  }
});
