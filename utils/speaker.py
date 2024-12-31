import pyttsx3
import time

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

    # Queue the sentences for speaking
    for sentence in sentences:
        engine.say(sentence)
    
    # Start the speaking process in non-blocking mode
    print("Starting text-to-speech...")
    engine.startLoop(False)

    # Simulate other tasks while speaking
    try:
        for i in range(5):
            print(f"Doing other tasks... {i}")
            time.sleep(1)
            # Allow engine to process queued speech
            engine.iterate()
    finally:
        # Stop the engine
        print("Stopping the engine...")
        engine.endLoop()

if __name__ == "__main__":
    main()
