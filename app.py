from flask import Flask, render_template, request, jsonify
import os
import json
import time
from markov_chain import MarkovChainTextGenerator

app = Flask(__name__)

# Initialize the Markov Chain text generator
text_generator = MarkovChainTextGenerator()

# Path to text sources
SOURCES_DIR = os.path.join(os.path.dirname(__file__), 'sources')

# For performance monitoring
request_times = {}

# Ensure sources directory exists
os.makedirs(SOURCES_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Generate word predictions based on input text."""
    start_time = time.time()
    
    data = request.json
    text = data.get('text', '')
    
    # Get suggestions and the order of the Markov Chain used
    suggestions, order = text_generator.predict_next_words(text, num_suggestions=3)
    
    # Log request time for performance monitoring
    elapsed = time.time() - start_time
    request_times['predict'] = elapsed
    
    # Print performance info
    print(f"Prediction request processed in {elapsed:.4f} seconds")
    
    return jsonify({
        'suggestions': suggestions,
        'order': order
    })

@app.route('/sources', methods=['GET'])
def get_sources():
    """Get all available text sources with status."""
    sources = [{
        'name': name,
        'active': active
    } for name, active in text_generator.sources.items()]
    return jsonify({'sources': sources})

@app.route('/toggle_source', methods=['POST'])
def toggle_source():
    """Toggle a text source on or off."""
    data = request.json
    source = data.get('source', '')
    active = data.get('active', True)
    
    success = text_generator.toggle_source(source, active)
    
    return jsonify({
        'success': success
    })

def load_initial_sources():
    """Load initial text sources from the sources directory."""
    if not os.path.exists(SOURCES_DIR):
        os.makedirs(SOURCES_DIR)
        # Create a sample text file if no sources exist
        create_sample_sources()
    
    # Load all .txt files from the sources directory
    return text_generator.load_sources_from_directory(SOURCES_DIR)

def create_sample_sources():
    """Create sample text files if no sources exist."""
    # Sample text from Pride and Prejudice
    sample1 = """
    It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.
    However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters.
    "My dear Mr. Bennet," said his lady to him one day, "have you heard that Netherfield Park is let at last?"
    Mr. Bennet replied that he had not.
    "But it is," returned she; "for Mrs. Long has just been here, and she told me all about it."
    Mr. Bennet made no answer.
    "Do you not want to know who has taken it?" cried his wife impatiently.
    "You want to tell me, and I have no objection to hearing it."
    This was invitation enough.
    """
    
    # Sample text from Alice in Wonderland
    sample2 = """
    Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, "and what is the use of a book," thought Alice "without pictures or conversations?"
    So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.
    There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, "Oh dear! Oh dear! I shall be late!" (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.
    """
    
    # Write sample files
    with open(os.path.join(SOURCES_DIR, 'sample1.txt'), 'w', encoding='utf-8') as file:
        file.write(sample1)
    
    with open(os.path.join(SOURCES_DIR, 'sample2.txt'), 'w', encoding='utf-8') as file:
        file.write(sample2)

if __name__ == '__main__':
    # Load initial sources
    loaded_sources = load_initial_sources()
    print(f"Loaded sources: {', '.join(loaded_sources)}")
    
    # Run the Flask app
    app.run(debug=True)