from pydub import AudioSegment
from io import BytesIO
import numpy as np
import os
import json
from flask import Flask, request, make_response
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route('/process', methods=['POST'])
def process():
    """
    Censor audio based on provided indexes.
    
    Expects multipart/form-data with:
      - 'to_censor': audio file (WAV format)
      - 'indexes': JSON array of [start, end] tuples (relative positions 0-1)
    Returns:
      censored audio file (WAV format)
    """
    try:
        # Check if required files were provided
        if 'indexes' not in request.files or 'to_censor' not in request.files:
            return make_response("Missing required files: 'indexes' and 'to_censor'", 400)
            
        indexes_file = request.files['indexes']
        audio_file = request.files['to_censor']
        
        # Validate files
        if indexes_file.filename == '' or audio_file.filename == '':
            return make_response("No selected file", 400)
            
        # Load indexes; these are expected as fractions (start, end)
        indexes = json.load(indexes_file)
        
        # For debugging, log file size and number of indexes
        audio_file.seek(0, os.SEEK_END)
        file_length = audio_file.tell()
        audio_file.seek(0)
        logging.info(f"Input filesize: {file_length} bytes")
        logging.info(f"Number of censorship intervals received: {len(indexes)}")
        
        # Load audio via pydub
        speech = AudioSegment.from_wav(audio_file)
        samples = np.array(speech.get_array_of_samples())
        total_samples = len(samples)
        logging.info(f"Total audio samples: {total_samples}")
        
        # Set a shrink factor to shorten each censorship interval.
        # Lower factors will mute a smaller portion of the interval.
        shrink_factor = 0.4  # Adjust this value as needed
        
        # Process each interval
        for original_interval in indexes:
            orig_start, orig_end = original_interval
            original_duration_fraction = orig_end - orig_start
            midpoint = (orig_start + orig_end) / 2
            # Compute the new interval: smaller than the original interval.
            new_duration_fraction = original_duration_fraction * shrink_factor
            new_start = midpoint - new_duration_fraction / 2
            new_end = midpoint + new_duration_fraction / 2
            
            # Map the fractional positions to sample indices.
            start_sample = int(new_start * total_samples)
            end_sample = int(new_end * total_samples)
            
            logging.info(
                f"Original interval: {original_interval} -> Adjusted interval: ({new_start:.4f}, {new_end:.4f}) "
                f"which maps to samples ({start_sample}, {end_sample})"
            )
            
            # Zero out the samples in the adjusted interval.
            samples[start_sample:end_sample] = 0
        
        # Create a new audio segment from the modified samples.
        new_sound = speech._spawn(samples)
        outputfile = BytesIO()
        new_sound.export(outputfile, format="wav")
        outputfile.seek(0)
        output_data = outputfile.getvalue()
        logging.info(f"Output filesize: {len(output_data)} bytes")
        
        # Create and return the response
        response = make_response(output_data)
        response.headers.set('Content-Type', 'audio/wav')
        return response
        
    except json.JSONDecodeError:
        return make_response("Invalid JSON in indexes file", 400)
    except Exception as e:
        logging.error(f"Error processing audio: {str(e)}", exc_info=True)
        return make_response(f"Error processing audio: {str(e)}", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
