import os
import time
import speech_recognition as sr
import google.generativeai as genai
from flask import Flask, render_template, jsonify, request, url_for
from dotenv import load_dotenv
from murf import Murf, MurfRegion
from deepgram import DeepgramClient, PrerecordedOptions

app = Flask(__name__)
load_dotenv()

# --- CONFIGURATION ---
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY") 
MURF_VOICE_ID = "en-US-caleb" 

# --- CLIENT SETUP ---
# 1. Gemini
genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

# 2. Murf
murf_client = Murf(api_key=MURF_API_KEY, region=MurfRegion.GLOBAL)

# 3. Deepgram
try:
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
except Exception as e:
    print(f"Deepgram Init Error: {e}")

# Ensure audio directory exists
AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Global variable to store current session topic
current_topic = "General Python"

def get_ai_response(user_text):
    print(f"DEBUG: Sending to Gemini ({current_topic}) -> {user_text}")
    try:
        prompt = (
            f"You are a friendly technical interviewer named CodeCoach. "
            f"The user has chosen to practice: '{current_topic}'. "
            "Keep your answers concise (maximum 2 sentences) so they work well for voice. "
            "If the user says 'ready', start with a question about the topic. "
            f"User says: {user_text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return "I'm having trouble connecting to my brain right now."

def generate_falcon_audio(text):
    """Generates audio file using Murf Falcon Streaming."""
    filename = f"response_{int(time.time())}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    
    try:
        # Using FALCON model for ultra-low latency
        audio_stream = murf_client.text_to_speech.stream(
            text=text,
            voice_id=MURF_VOICE_ID,
            model="FALCON",
            format="MP3",
            multi_native_locale="en-US"
        )
        with open(filepath, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)
        return filename
    except Exception as e:
        print(f"Murf Error: {e}")
        return None

def listen_to_mic():
    """Captures audio via PyAudio and sends to Deepgram API."""
    r = sr.Recognizer()
    try:
        # CRITICAL: Use device_index=2 based on your setup. 
        # If it stops working, check 'python check_mics.py' again.
        with sr.Microphone(device_index=2) as source:
            print("Listening (Deepgram)...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            
            # 1. Capture Raw Audio
            audio = r.listen(source, timeout=4, phrase_time_limit=8)
            audio_data = audio.get_wav_data()
            
            # 2. Send to Deepgram for Transcription
            payload = {'buffer': audio_data}
            options = PrerecordedOptions(
                model="nova-2",      # Deepgram's fastest model
                smart_format=True,
                language="en"
            )
            
            # Updated to use .listen.rest instead of .listen.prerecorded to fix deprecation warning
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
            transcript = response.results.channels[0].alternatives[0].transcript
            
            print(f"Deepgram Heard: {transcript}")
            return transcript

    except sr.WaitTimeoutError:
        print("Timeout: No speech detected.")
        return None
    except Exception as e:
        print(f"Mic/Deepgram Error: {e}")
        return None

# --- FLASK ROUTES ---

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/set_topic", methods=["POST"])
def set_topic():
    global current_topic
    data = request.json
    current_topic = data.get("topic", "General Python")
    print(f"Topic changed to: {current_topic}")
    
    welcome_text = f"Great. I am ready to interview you on {current_topic}. Say ready when you are."
    audio_file = generate_falcon_audio(welcome_text)
    
    if audio_file:
        audio_url = url_for('static', filename=f'audio/{audio_file}')
        return jsonify({"status": "success", "message": welcome_text, "audio_url": audio_url})
    else:
        return jsonify({"status": "error", "message": "Audio generation failed"})

@app.route("/process_interaction", methods=["POST"])
def process_interaction():
    # Check if text input is provided in the request
    data = request.get_json(silent=True)
    user_text = None
    
    if data and "text" in data:
        user_text = data["text"]
        print(f"User Typed: {user_text}")
    else:
        # 1. Listen (Deepgram)
        user_text = listen_to_mic()
    
    if not user_text:
        return jsonify({"status": "error", "message": "No speech or text detected"})

    # 2. Think (Gemini)
    ai_response = get_ai_response(user_text)

    # 3. Speak (Murf Falcon)
    audio_file = generate_falcon_audio(ai_response)
    
    if not audio_file:
         return jsonify({"status": "error", "message": "Audio generation failed"})

    # 4. Return to UI
    audio_url = url_for('static', filename=f'audio/{audio_file}')
    return jsonify({
        "status": "success",
        "user_text": user_text,
        "ai_text": ai_response,
        "audio_url": audio_url
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)