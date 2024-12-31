import pyttsx3
import threading
import time

def speak_repeatedly(engine, text, interval):
    """Speak a sentence repeatedly at a specific time interval."""
    while True:
        engine.say(text)
        engine.runAndWait()
        time.sleep(interval)

def main():
    # Initialize the pyttsx3 engine
    engine = pyttsx3.init()

    # Set properties (optional)
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  # Use the first voice (male in most systems)

    # Sentence to repeat and interval in seconds
    sentence = "This is a repeated message."
    interval = 5  # Repeat every 5 seconds

    # Create and start a thread for the repeating speech
    tts_thread = threading.Thread(target=speak_repeatedly, args=(engine, sentence, interval))
    tts_thread.daemon = True  # Allow program to exit even if thread is running
    tts_thread.start()

    # Simulate other tasks in the main thread
    print("Starting text-to-speech in non-blocking mode. Press Ctrl+C to stop.")
    try:
        while True:
            print("Main thread is running other tasks...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping text-to-speech.")

if __name__ == "__main__":
    main()
