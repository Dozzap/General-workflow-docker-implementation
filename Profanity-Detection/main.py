import re
from better_profanity import profanity
from flask import Flask, request, jsonify

app = Flask(__name__)

def clean_text(text):
    """Normalize text by removing special characters (except spaces) and ensuring words are separated."""
    text = re.sub(r"[^\w\s]", " ", text)  # Replace special characters with space
    return text.lower().strip()

def filter_text(text, char="*"):
    """Censor text using better_profanity"""
    return profanity.censor(text, char)

def extract_indexes(original, censored, char="*"):
    """Find where words were censored"""
    indexes = []
    in_word = False
    start = 0
    for index, (orig_char, cens_char) in enumerate(zip(original, censored)):
        if orig_char != cens_char:  # Found a censored word
            if not in_word:
                in_word = True
                start = index
        else:
            if in_word:
                in_word = False
                indexes.append((start / len(original), index / len(original)))
    return indexes

@app.route('/process', methods=['POST'])
def detect_profanity():
    """Detect and censor profanity, returning original, cleaned, and censored text"""
    try:
        data = request.get_json()
        message = data.get('message', 'Hello World!')

        cleaned_message = clean_text(message)
        profanity.load_censor_words()  # Load default wordlist
        censored_message = filter_text(cleaned_message)
        indexes = extract_indexes(cleaned_message, censored_message)

        print(f"Original: {message}")
        print(f"Cleaned: {cleaned_message}")
        print(f"Censored: {censored_message}")
        print(f"Profanity Count: {len(indexes)}")

        return jsonify(
            original_text=message,
            cleaned_text=cleaned_message,
            censored_text=censored_message,
            indexes=indexes
        )

    except Exception as e:
        print(f"Error detecting profanity: {str(e)}")
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
