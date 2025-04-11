import re
import os
import tempfile
import logging
import traceback
from pydub import AudioSegment
from better_profanity import profanity
from flask import Flask, request, jsonify, make_response
import speech_recognition as sr  

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_text(text):
    """Normalize text by removing special characters (except spaces) and ensuring words are separated."""
    text = re.sub(r"[^\w\s]", " ", text)  # Replace special characters with space
    return text.lower().strip()

def filter_text(text, char="*"):
    """Censor text using better_profanity."""
    return profanity.censor(text, char)

def extract_indexes(original, censored, char="*"):
    """Find indexes (as fractions of the total string length) where words were censored."""
    indexes = []
    in_word = False
    start = 0
    for index, (orig_char, cens_char) in enumerate(zip(original, censored)):
        if orig_char != cens_char:
            if not in_word:
                in_word = True
                start = index
        else:
            if in_word:
                in_word = False
                indexes.append((start / len(original), index / len(original)))
    return indexes

@app.route('/process', methods=['POST'])
def detect_profanity_from_audio():
    try:
        if not request.data:
            return make_response("No audio data provided", 400)

        # Save the incoming audio data to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            temp_filename = tmp_audio.name
            tmp_audio.write(request.data)
        logging.info(f"Temporary file created: {temp_filename}")

        # Log the first 12 bytes (header) of the file for debugging
        with open(temp_filename, "rb") as f:
            header = f.read(12)
        logging.info(f"Audio file header: {header}")

        # Check if the header starts with 'RIFF'
        if not header.startswith(b"RIFF"):
            logging.error("Audio file does not start with 'RIFF'; it may not be a valid WAV file.")
            os.remove(temp_filename)
            return make_response("Invalid audio format: expected PCM WAV", 400)

        # Use speech recognition to convert audio to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_filename) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        logging.info(f"Recognized text: {text}")

        # Process text: clean and censor
        cleaned_message = clean_text(text)
        profanity.load_censor_words()  # Loads the default profanity list
        censored_message = filter_text(cleaned_message)
        indexes = extract_indexes(cleaned_message, censored_message)
        logging.info(f"Cleaned text: {cleaned_message}")
        logging.info(f"Censored text: {censored_message}")
        logging.info(f"Censorship indexes: {indexes}")

        
        audio_segment = AudioSegment.from_file(temp_filename, format="wav")
        duration = len(audio_segment) / 1000.0  # Duration in seconds
        logging.info(f"Audio file duration: {duration} seconds")


        # Clean up temporary file
        os.remove(temp_filename)
        logging.info(f"Temporary file {temp_filename} removed.")

        # Return the result as JSON
        return jsonify(
            original_text=text,
            cleaned_text=cleaned_message,
            censored_text=censored_message,
            indexes=indexes
        )

    except Exception as e:
        logging.error(f"Error detecting profanity: {str(e)}\n{traceback.format_exc()}")
        return make_response(jsonify({"error": "Internal Server Error", "details": str(e)}), 500)

if __name__ == '__main__':
    logging.info("🚀 Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000)
