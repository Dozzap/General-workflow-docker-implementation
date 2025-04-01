from pydub import AudioSegment
from io import BytesIO
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def convert_audio():
    """Convert MP3 to WAV
    Expects raw MP3 data in request body
    Returns:
        converted audio file (WAV format)
    """
    try:
        if not request.data:
            return make_response("No audio data provided", 400)
            
        input = BytesIO(request.data)
        inputSize = len(input.getvalue())
        print(f"Input filesize: {inputSize}")
        
        # Convert MP3 to WAV
        speech = AudioSegment.from_mp3(input)
        output = BytesIO()
        speech.export(output, format="wav")
        
        print(f"Output filesize: {len(output.getvalue())}")
        
        response = make_response(output.getvalue())
        response.headers.set('Content-Type', 'audio/wav')
        return response
        
    except Exception as e:
        print(f"Error converting audio: {str(e)}")
        return make_response(f"Error converting audio: {str(e)}", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)