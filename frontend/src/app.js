/**
 * AI Meeting Assistant
 * Main application script
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize meeting service
    meetingService.initialize();
    
    // Set up platform selection default
    const defaultPlatformBtn = document.querySelector('.platform-btn[data-platform="default"]');
    if (defaultPlatformBtn) {
        defaultPlatformBtn.click();
    }
    
    console.log('AI Meeting Assistant initialized');
});

// Function to simulate an answer (for testing without backend)
function simulateAnswer() {
    const questions = [
        "What is the project timeline?",
        "Who is responsible for the front-end development?",
        "Where will we host the application?",
        "How do we handle the audio processing?"
    ];
    
    const answers = [
        "Based on the discussion, the project timeline aims for completion within the next 6-8 weeks, with an initial prototype due in 2 weeks.",
        "Sarah will lead the front-end development team, collaborating with design to implement the user interface.",
        "The application will be hosted on AWS using their EC2 instances for the backend and S3 for static content.",
        "Audio processing is handled through a WebRTC pipeline with noise suppression and echo cancellation before being sent to the transcription service."
    ];
    
    const randomIndex = Math.floor(Math.random() * questions.length);
    
    meetingService.handleAnswer({
        question: questions[randomIndex],
        answer: answers[randomIndex],
        timestamp: new Date().toISOString()
    });
}

// For testing purposes - comment out in production
window.simulateAnswer = simulateAnswer;
