from pydub import AudioSegment
from io import BytesIO
import os
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def compress_audio():
    """Compress audio by reducing quality
    Expects multipart/form-data with:
    - 'to_compress': audio file (WAV format)
    Returns:
        compressed audio file (WAV format)
    """
    try:
        if 'to_compress' not in request.files:
            return make_response("Missing required file: 'to_compress'", 400)
            
        file = request.files['to_compress']
        
        if file.filename == '':
            return make_response("No selected file", 400)
            
        # Measure input size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        print(f"Input filesize: {file_length}")
        
        # Process audio
        outputfile = BytesIO()
        speech = AudioSegment.from_wav(file)
        speech = speech.set_frame_rate(5000)  # Reduce frame rate
        speech = speech.set_sample_width(1)   # Reduce sample width
        speech.export(outputfile, format="wav")
        
        print(f"Output filesize: {len(outputfile.getvalue())}")
        
        response = make_response(outputfile.getvalue())
        response.headers.set('Content-Type', 'audio/wav')
        return response
        
    except Exception as e:
        print(f"Error compressing audio: {str(e)}")
        return make_response(f"Error compressing audio: {str(e)}", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
