from pydub import AudioSegment
from io import BytesIO
import numpy as np
import os
import json
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    """Censor audio based on provided indexes
    Expects multipart/form-data with:
    - 'to_censor': audio file (WAV format)
    - 'indexes': JSON array of [start, end] tuples (relative positions 0-1)
    Returns:
        censored audio file (WAV format)
    """
    try:
        # Check if files were provided
        if 'indexes' not in request.files or 'to_censor' not in request.files:
            return make_response("Missing required files: 'indexes' and 'to_censor'", 400)
            
        indexes_file = request.files['indexes']
        audio_file = request.files['to_censor']
        
        # Validate files
        if indexes_file.filename == '' or audio_file.filename == '':
            return make_response("No selected file", 400)
            
        # Process the files
        indexes = json.load(indexes_file)
        
        # find out length of file
        audio_file.seek(0, os.SEEK_END)
        file_length = audio_file.tell()
        # reset file
        audio_file.seek(0)
        
        print(f"Input filesize: {file_length}")
        print(f"Length of Input-Indexes: {len(indexes)}")
        
        outputfile = BytesIO()
        speech = AudioSegment.from_wav(audio_file)
        
        samples = np.array(speech.get_array_of_samples())
        
        # Efficient implementation (uncomment to use)
        for start, end in indexes:
            start_sample = int(start * len(samples))
            end_sample = int(end * len(samples))
            samples[start_sample:end_sample] = 0
        
        # Inefficient implementation (current)
        # for index, s in enumerate(samples):
        #     for start, end in indexes:
        #         start_sample = int(start * len(samples))
        #         end_sample = int(end * len(samples))
        #         if start_sample < index < end_sample:
        #             samples[index] = 0
        
        new_sound = speech._spawn(samples)
        new_sound.export(outputfile, format="wav")
        
        # print file lengths
        print(f"Output filesize: {len(outputfile.getvalue())}")
        
        # Create response
        response = make_response(outputfile.getvalue())
        response.headers.set('Content-Type', 'audio/wav')
        return response
        
    except json.JSONDecodeError:
        return make_response("Invalid JSON in indexes file", 400)
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return make_response(f"Error processing audio: {str(e)}", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)