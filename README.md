CodeCoach: The AI Interviewer
Submission for Techfest 2025-26 MurfVoice Agent Hackathon
CodeCoach is a real-time, voice-interactive technical interviewer designed to help students master Python. 
It replaces the anxiety of mock interviews with a friendly, ultra-fast AI coach that listens to your voice, evaluates your answers, and provides instant vocal feedback.
Key Features
Ultra-Low Latency: Powered by the Murf Falcon Streaming API, ensuring the AI speaks back instantly without the "robotic pause."
Real-TimeVoice Input: Integrated with Deepgram Nova-2 for high-precision speech-totext, capable of understanding technical jargon (e.g., "tuple," "recursion").
Intelligent Feedback: Uses Google Gemini 2.0 Flash to grade answers, ask follow-up questions, and adapt to the user's skill level.
Topic Selection: Users can switch between "Python Basics," "Data Structures," "Machine Learning," and "System Design."
CodeVisualizer: The frontend features a live code syntax highlighter and an audio visualizer that animates while the AI speaks.
Transcript Download: Users can download their entire interview session for review.
Tech Stack
Frontend: HTML5, CSS3, JavaScript (with highlight.js & marked.js )
Backend: Flask (Python)
Text-to-Speech (TTS): Murf Falcon API (Streaming Endpoint)
Speech-to-Text (ASR): Deepgram Nova-2
LLM (Brain): Google Gemini 2.0 Flash
Setup Instructions
1. Clone the Repository
git clone [https://github.com/paramshinde/Code-Coach.git](https://github.com/paramshinde/Co
cd Code-Coach
2. Install Dependencies
12/5/25, 7:58 PM Google Gemini
https://gemini.google.com/app/7afd2c725165df3e?is_sa=1&is_sa=1&android-min-version=301356232&ios-min-version=322.0&campaign_id=bkw s&… 1/3
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the root directory. Do not upload this file to GitHub.
# Murf AI (Required for TTS)
MURF_API_KEY=your_murf_api_key_here
# Deepgram (Required for ASR)
DEEPGRAM_API_KEY=your_deepgram_key_here
# Google Gemini (Required for Logic)
GEMINI_API_KEY=your_gemini_key_here
4. Run the Application
python app.py
Open your browser and navigate to http://127.0.0.1:5000 .
API Integration Details
Murf Falcon (TTS)
We strictly utilize the streaming endpoint to satisfy the hackathon's low-latency requirement.
Model: FALCON
Voice ID: en-US-caleb (Conversational)
Endpoint: murf_client.text_to_speech.stream
Deepgram (ASR)
We use the Nova-2 model via the transcribe_file method for speed and accuracy.
Google Gemini (LLM)
We rely on the Gemini 2.0 Flash model for sub-second generation of technical interview questions.
🎥Demo Video
[Link to Demo Video] (Please update this link after uploading your video!)
Built by Param Shinde for Techfest 2025-26.
12/5/25, 7:58 PM Google Gemini
https://gemini.google.com/app/7afd2c725165df3e?is_sa=1&is_sa=1&android-min-version=301356232&ios-min-version=322.0&campaign_id=bkw s&… 2/3
12/5/25, 7:58 PM Google Gemini
https://gemini.google.com/app/7afd2c725165df3e?is_sa=1&is_sa=1&android-min-version=301356232&ios-min-version=322.0&campaign_id=bkw s&… 3/3

