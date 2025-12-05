import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


MURF_API_URL = "https://api.murf.ai/v1/speech/stream" 


MURF_VOICE_ID = "en-US-caleb"


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("CodeCoach: Using Gemini 1.5 Flash")
except:
    model = genai.GenerativeModel('gemini-pro')
    print("CodeCoach: Using Gemini Pro")

def get_ai_response(user_text):
    try:
        prompt = (
            "You are a friendly Python technical interviewer named CodeCoach. "
            "Keep your answers concise (maximum 2 sentences). "
            f"User says: {user_text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "I'm having trouble thinking right now."

def text_to_speech_murf(text):
    headers = {
        "api-key": os.getenv("MURF_API_KEY").strip(),
        "Content-Type": "application/json"
    }

    payload = {
        "voiceId": MURF_VOICE_ID,
        "text": text,
        "model": "FALCON",      # Critical for the hackathon
        "format": "MP3",        # Request MP3 format
        "multiNativeLocale": "en-US" # Required for Falcon usually
    }

    try:
        # Note: We use the new MURF_API_URL defined at the top
        response = requests.post(MURF_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            with open("output.mp3", "wb") as f:
                f.write(response.content)
            
            # Windows Command to play audio
            os.system("start output.mp3")
        else:
            print(f"Murf API Error ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"Audio Playback Error: {e}")
        
import speech_recognition as sr

def listen_to_user():
    """Captures audio from the microphone and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone(device_index=2) as source:
        print("\n🎤 Listening... (Speak now)")
        # Adjust for ambient noise helps if you are in a noisy room
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing audio...")
            text = r.recognize_google(audio) # Uses Google's free speech API
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⚠️ No speech detected.")
            return None
        except sr.UnknownValueError:
            print("⚠️ Could not understand audio.")
            return None
        except Exception as e:
            print(f"Microphone Error: {e}")
            return None

# Create a list to store the conversation
conversation_history = []

def generate_feedback_report():
    """Asks Gemini to grade the interview."""
    print("\n📝 Generating Feedback Report... Please wait.")
    
    history_text = "\n".join(conversation_history)
    prompt = (
        "You are a senior technical interviewer. Based on the following interview transcript, "
        "provide a brief feedback report. Include:\n"
        "1. A score out of 10.\n"
        "2. One strength.\n"
        "3. One area for improvement.\n"
        "Keep it strictly under 4 sentences.\n\n"
        f"TRANSCRIPT:\n{history_text}"
    )
    
    try:
        feedback = model.generate_content(prompt).text
        print("\n" + "="*40)
        print("INTERVIEW FEEDBACK REPORT")
        print("="*40)
        print(feedback)
        
        # Optional: Speak the feedback too!
        text_to_speech_murf(f"Here is your feedback. {feedback}")
        
    except Exception as e:
        print(f"Feedback Error: {e}")

def main():
    print(f"--- CodeCoach Started (Voice: {MURF_VOICE_ID}) ---")
    print("Tip: Say 'Exit' or 'Stop' to end the interview and get feedback.")
    
    # Initial Greeting
    intro = "Hello! I am Code Coach. I'm ready to interview you on Python. Are you ready?"
    print(f"CodeCoach: {intro}")
    text_to_speech_murf(intro)
    conversation_history.append(f"AI: {intro}")

    while True:
        # OPTION: Toggle between Voice and Text
        # Use listen_to_user() for the video demo!
        # Use input() for debugging if your mic breaks.
        
        # user_input = input("\nYou (Type): ") 
        user_input = listen_to_user() # <--- NEW VOICE FUNCTION
        
        if not user_input:
            continue # Skip loop if no audio detected

        if user_input.lower() in ["exit", "quit", "stop"]:
            generate_feedback_report()
            break
        
        # Log user input
        conversation_history.append(f"User: {user_input}")
        
        # Get AI Response
        ai_response = get_ai_response(user_input)
        print(f"CodeCoach: {ai_response}")
        
        # Log AI response
        conversation_history.append(f"AI: {ai_response}")
        
        # Speak
        text_to_speech_murf(ai_response)

if __name__ == "__main__":
    main()