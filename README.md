# AI Meeting Assistant
**AI-powered real-time meeting assistant**

An AI-powered real-time meeting assistant that listens to questions during meetings and automatically displays answers on your screen.

## Features

- **Real-time Audio Processing**: Captures and processes audio from meetings
- **Question Detection**: Uses NLP to identify questions in conversation
- **AI-powered Answers**: Generates relevant answers using OpenAI's GPT-4
- **Platform Integration**: Works with Zoom, Google Meet, Microsoft Teams, and system microphone
- **Minimal UI**: Non-intrusive interface that displays answers without disrupting your meeting

## Architecture

The application consists of two main components:

### Backend

- **Audio Capture**: Processes meeting audio and transcribes it to text
- **Question Detection**: Analyzes text to identify questions
- **Answer Generation**: Produces relevant answers to detected questions
- **Platform Integration**: Connects to various meeting platforms

### Frontend

- **WebSocket Connection**: Real-time communication with the backend
- **Answer Display**: Shows questions and answers in a clean interface
- **Settings Management**: Configure API keys and display preferences
- **Platform Selection**: Choose which meeting platform to connect to

## Prerequisites

- Python 3.8+
- OpenAI API key (for answer generation)
- Web browser with WebSocket support

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/ai-meeting-assistant.git
   cd ai-meeting-assistant
   ```

2. Set up the backend:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Start the backend server:
   ```
   python main.py
   ```

5. Open the frontend:
   - Navigate to the `frontend` directory
   - Open `index.html` in your web browser
   - Alternatively, you can serve it using a simple HTTP server:
     ```
     cd frontend
     python -m http.server 8080
     ```
     Then visit `http://localhost:8080` in your browser

## Usage

1. Open the AI Meeting Assistant in your browser
2. Select your meeting platform (Zoom, Teams, Meet, or System Mic)
3. Enter the meeting ID if required (not needed for system microphone)
4. Click "Connect" to start the assistant
5. The assistant will now listen for questions and display answers in real-time
6. You can customize the display settings by clicking on "Settings" in the footer

## Privacy Considerations

- Audio is processed locally and only transmitted to OpenAI for transcription and question answering
- No audio is stored permanently
- The application does not record entire meetings, only processes audio to detect questions

## Limitations

- Currently requires manual setup of platform integrations
- Performance may vary based on audio quality and background noise
- Answer quality depends on the context available in the recent conversation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by services like [SenseiCopilot](https://senseicopilot.com) and [FinalRound AI](https://finalroundai.com)
- Uses OpenAI's GPT-4 for answer generation
- Built with FastAPI and WebSockets for real-time communication
