from pydub import AudioSegment
from io import BytesIO
from flask import Flask, request, make_response
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route('/process', methods=['POST'])
def convert_audio():
    """Convert MP3 to WAV.
    
    Expects raw MP3 data in the request body.
    Returns the converted audio file (WAV format).
    """
    try:
        if not request.data:
            return make_response("No audio data provided", 400)
            
        # Wrap the raw MP3 data in a BytesIO object
        input_stream = BytesIO(request.data)
        input_data = input_stream.getvalue()
        logging.info(f"Input filesize: {len(input_data)} bytes")
        
        # Convert MP3 to WAV using pydub
        speech = AudioSegment.from_mp3(input_stream)
        output_stream = BytesIO()
        speech.export(output_stream, format="wav")
        output_data = output_stream.getvalue()
        logging.info(f"Output filesize: {len(output_data)} bytes")
        
        # Log the audio duration in seconds (pydub returns duration in milliseconds)
        duration_sec = len(speech) / 1000.0
        logging.info(f"Audio duration: {duration_sec:.2f} seconds")
        
        # Create and return the response with correct Content-Type
        response = make_response(output_data)
        response.headers.set('Content-Type', 'audio/wav')
        return response
        
    except Exception as e:
        logging.error(f"Error converting audio: {str(e)}")
        return make_response(f"Error converting audio: {str(e)}", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
