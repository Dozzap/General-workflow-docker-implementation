
import logging
import traceback

import pyttsx3
from flask import Flask, request, make_response, jsonify
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize pyttsx3 engine (Offline TTS)
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust speed (default: 200)
engine.setProperty('volume', 1.0)  # Adjust volume (0.0 to 1.0)

@app.route('/process', methods=['POST'])
def text_to_speech():
    try:
        logging.info(f"Received request with content-type: {request.content_type}")

        # Ensure JSON request
        if not request.is_json:
            logging.warning("Invalid request: Expected JSON with 'message' field.")
            return make_response(jsonify({"error": "Invalid request. Expected JSON with 'message' field."}), 400)

        data = request.get_json()
        if 'message' not in data:
            logging.warning("Missing 'message' field in request.")
            return make_response(jsonify({"error": "Missing 'message' field."}), 400)

        message = data['message']
        logging.info(f"Processing message: {message}")



        # Convert text to speech (Offline)
        audio_fp = BytesIO()
        engine.save_to_file(message, 'temp_audio.mp3')  # Save to file
        engine.runAndWait()

        # Read file into memory
        with open("temp_audio.mp3", "rb") as f:
            audio_data = f.read()

        # Send audio response
        response = make_response(audio_data)
        response.headers.set('Content-Type', 'audio/mpeg')
        response.headers.set('Content-Disposition', 'attachment; filename="speech.mp3"')

        logging.info("✅ Text-to-Speech conversion successful, returning audio file.")
        return response

    except Exception as e:
        logging.error(f"❌ Error: {str(e)}\n{traceback.format_exc()}")
        return make_response(jsonify({"error": "Internal Server Error", "details": str(e)}), 500)

if __name__ == '__main__':
    logging.info("🚀 Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)

