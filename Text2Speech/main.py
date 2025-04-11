import logging
import traceback
import os
import tempfile
import re

import pyttsx3
from flask import Flask, request, make_response, jsonify
from pydub import AudioSegment

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize pyttsx3 engine (Offline TTS)
engine = pyttsx3.init()
engine.setProperty('rate', 140)    # Adjust speech rate
engine.setProperty('volume', 1.0)    # Adjust volume (0.0 to 1.0)

def split_into_sentences(text):
    """
    Splits text into sentences, preserving punctuation at the end.
    It uses regex to split on punctuation (., !, or ?) followed by whitespace.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

@app.route('/process', methods=['POST'])
def text_to_speech():
    try:
        logging.info(f"Received request with content-type: {request.content_type}")

        # Ensure request is JSON with a 'message' field.
        if not request.is_json:
            logging.warning("Invalid request: Expected JSON with 'message' field.")
            return make_response(jsonify({"error": "Invalid request. Expected JSON with 'message' field."}), 400)

        data = request.get_json()
        if 'message' not in data:
            logging.warning("Missing 'message' field in request.")
            return make_response(jsonify({"error": "Missing 'message' field."}), 400)

        message = data['message']
        logging.info(f"Processing message (length {len(message)} characters): {message}")

        # Split text into sentences.
        sentences = split_into_sentences(message)
        logging.info(f"Split text into {len(sentences)} sentence(s).")

        # Create an empty AudioSegment for concatenation.
        full_audio = AudioSegment.empty()
        # Define a 250 ms silent gap between sentences.
        gap = AudioSegment.silent(duration=200)

        # Process each sentence individually.
        for i, sentence in enumerate(sentences):
            logging.info(f"Processing sentence {i+1}/{len(sentences)}: {sentence}")

            # Create a temporary file for this sentence.
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_filename = tmp.name
            logging.info(f"Temporary file created for sentence {i+1}: {temp_filename}")

            # Convert text to speech for this sentence.
            engine.save_to_file(sentence, temp_filename)
            engine.runAndWait()

            # Log the file size for debugging.
            file_size = os.path.getsize(temp_filename)
            logging.info(f"Sentence {i+1} audio file size: {file_size} bytes")
            
            # Load generated audio into a pydub AudioSegment.
            try:
                sentence_audio = AudioSegment.from_mp3(temp_filename)
            except Exception as conv_e:
                logging.error(f"Error loading audio for sentence {i+1}: {conv_e}")
                os.remove(temp_filename)
                continue

            # Append the sentence's audio and a silent gap.
            full_audio += sentence_audio  + gap

            # Clean up the temporary file.
            os.remove(temp_filename)
            logging.info(f"Temporary file {temp_filename} removed.")



        # Export the concatenated audio to a BytesIO buffer in MP3 format.
        output_buffer = tempfile.SpooledTemporaryFile()
        full_audio.export(output_buffer, format="mp3")
        output_buffer.seek(0)
        final_audio_data = output_buffer.read()
        output_buffer.close()

        logging.info(f"Text-to-Speech conversion successful; final audio size: {len(final_audio_data)} bytes.")
        logging.info(f"Audio duration: {len(full_audio) / 1000:.2f} seconds.")

        # Return the resulting MP3 file.
        response = make_response(final_audio_data)
        response.headers.set('Content-Type', 'audio/mpeg')
        response.headers.set('Content-Disposition', 'attachment; filename="speech.mp3"')
        return response

    except Exception as e:
        logging.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return make_response(jsonify({"error": "Internal Server Error", "details": str(e)}), 500)

if __name__ == '__main__':
    logging.info(" Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)