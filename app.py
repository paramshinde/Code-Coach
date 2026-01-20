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
genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except:
    model = genai.GenerativeModel('gemini-pro')

murf_client = Murf(api_key=MURF_API_KEY, region=MurfRegion.GLOBAL)

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
            "Keep your answers concise (maximum 2 sentences). "
            f"User says: {user_text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return "I'm having trouble connecting to my brain right now."

def generate_falcon_audio(text):
    filename = f"response_{int(time.time())}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    try:
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
    """Captures audio: Tries Deepgram first -> Falls back to Google."""
    r = sr.Recognizer()
    
    # Reduce the silence time required to consider the speech "done"
    r.pause_threshold = 0.6  # Default is 0.8
    # Reduce non-speaking duration to make it snappier
    r.non_speaking_duration = 0.3 # Default is 0.5
    
    try:
        # CRITICAL: Device Index 2 (Realtek)
        with sr.Microphone(device_index=2) as source:
            print("🎤 Listening...")
            # Reduce calibration time from 0.5 to 0.2 (Saves 300ms per turn)
            r.adjust_for_ambient_noise(source, duration=0.2)
            
            # OPTIMIZATION: Reduced limit from 8s to 5s to make uploads smaller/faster
            audio = r.listen(source, timeout=4, phrase_time_limit=5)
            
            # --- ATTEMPT 1: DEEPGRAM ---
            try:
                print("⚡ Sending to Deepgram...")
                audio_data = audio.get_wav_data()
                payload = {'buffer': audio_data}
                options = PrerecordedOptions(
                    model="nova-2", 
                    smart_format=True, 
                    language="en"
                )
                response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
                transcript = response.results.channels[0].alternatives[0].transcript
                
                if not transcript: raise ValueError("Empty Deepgram transcript")
                
                print(f"   Deepgram Heard: {transcript}")
                return transcript

            except Exception as dg_error:
                # --- ATTEMPT 2: GOOGLE FALLBACK ---
                print(f"    Deepgram Failed ({dg_error}). Switching to Google...")
                transcript = r.recognize_google(audio)
                print(f"   Google Heard: {transcript}")
                return transcript

    except sr.WaitTimeoutError:
        print("Timeout: No speech detected.")
        return None
    except Exception as e:
        print(f"Mic Error: {e}")
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/set_topic", methods=["POST"])
def set_topic():
    global current_topic
    data = request.json
    current_topic = data.get("topic", "General Python")
    welcome_text = f"Great. Ready to interview on {current_topic}."
    audio_file = generate_falcon_audio(welcome_text)
    return jsonify({"status": "success", "message": welcome_text, "audio_url": url_for('static', filename=f'audio/{audio_file}')})

@app.route("/process_interaction", methods=["POST"])
def process_interaction():
    data = request.get_json(silent=True)
    user_text = None
    
    if data and "text" in data:
        user_text = data["text"]
        print(f"User Typed: {user_text}")
    else:
        user_text = listen_to_mic()
    
    if not user_text:
        return jsonify({"status": "error", "message": "No speech detected. Try typing?"})

    ai_response = get_ai_response(user_text)
    audio_file = generate_falcon_audio(ai_response)
    
    if not audio_file:
        return jsonify({"status": "error", "message": "Audio generation failed"})

    return jsonify({
        "status": "success",
        "user_text": user_text,
        "ai_text": ai_response,
        "audio_url": url_for('static', filename=f'audio/{audio_file}')
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)