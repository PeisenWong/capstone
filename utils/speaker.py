import pyttsx3
import threading
import time

def speak(engine, text):
    """Function to handle text-to-speech in a separate thread."""
    engine.say(text)
    engine.runAndWait()

def on_start(name):
    print(f"Speech started: {name}")

def on_end(name, completed):
    print(f"Speech finished: {name} | Completed: {completed}")

def main():
    # Initialize the pyttsx3 engine
    engine = pyttsx3.init()

    # Connect event handlers
    engine.connect("started-utterance", on_start)
    engine.connect("finished-utterance", on_end)

    # Set properties (optional)
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  # Use the first voice (male in most systems)

    # Text to speak
    sentences = [
        "Hello, this is a test of pyttsx3 in non-blocking mode.",
        "This is the second sentence being spoken.",
        "Feel free to multitask while I speak!"
    ]

    # Create a thread for text-to-speech
    tts_thread = threading.Thread(target=lambda: speak(engine, " ".join(sentences)))
    tts_thread.start()

    # Simulate other tasks while speaking
    for i in range(5):
        print(f"Doing other tasks... {i}")
        time.sleep(1)

    # Wait for the text-to-speech thread to complete
    tts_thread.join()
    print("Text-to-speech task completed.")

if __name__ == "__main__":
    main()
