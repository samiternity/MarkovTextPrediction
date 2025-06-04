import os
import re
import random
import nltk
import time
from collections import defaultdict, Counter

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class MarkovChainTextGenerator:
    """
    A class that implements a Markov Chain for text prediction.
    Supports both first-order and second-order Markov Chains.
    """
    
    def __init__(self):
        # First-order Markov Chain: word -> {next_word: count}
        self.first_order_transitions = defaultdict(Counter)
        
        # Second-order Markov Chain: (word1, word2) -> {next_word: count}
        self.second_order_transitions = defaultdict(Counter)
        
        # Source management
        self.sources = {}  # source_name -> is_active
        self.source_contents = {}  # source_name -> content
        
        # Track total counts for calculating probabilities
        self.first_order_totals = defaultdict(int)
        self.second_order_totals = defaultdict(int)
        
        # Initialize with no sources
        self.is_trained = False
    
    def add_source(self, source_name, content, active=True):
        """Add a new text source to the Markov Chain model."""
        self.sources[source_name] = active
        self.source_contents[source_name] = content
        # Retrain model with all active sources
        self._train()
    
    def toggle_source(self, source_name, active):
        """Toggle a source on or off and retrain the model."""
        if source_name in self.sources:
            self.sources[source_name] = active
            self._train()
            return True
        return False
    
    def get_sources(self):
        """Return list of all source names."""
        return list(self.sources.keys())
    
    def _is_word(self, token):
        """Check if a token is a valid word (contains letters and is not just punctuation)."""
        # Must contain at least one letter and not be just punctuation
        return bool(re.search(r'[a-zA-Z]', token)) and len(token.strip()) > 0
    
    def _train(self):
        """Train the Markov Chain model using active sources."""
        start_time = time.time()
        print("Training Markov Chain model...")
        
        # Reset transition tables
        self.first_order_transitions = defaultdict(Counter)
        self.second_order_transitions = defaultdict(Counter)
        self.first_order_totals = defaultdict(int)
        self.second_order_totals = defaultdict(int)
        
        # Combine all active source text
        combined_text = ""
        for source_name, active in self.sources.items():
            if active:
                combined_text += self.source_contents[source_name] + " "
        
        if not combined_text.strip():
            self.is_trained = False
            print("No active sources to train from.")
            return
        
        print(f"Processing {len(combined_text)} characters of text...")
        
        # Tokenize text
        tokens = nltk.word_tokenize(combined_text)
        print(f"Tokenized into {len(tokens)} tokens")
        
        # Filter tokens to only include valid words
        word_tokens = [token.lower() for token in tokens if self._is_word(token)]
        print(f"Filtered to {len(word_tokens)} word tokens")
        
        # Build first-order transition table
        for i in range(len(word_tokens) - 1):
            curr_word = word_tokens[i]
            next_word = word_tokens[i + 1]
            
            self.first_order_transitions[curr_word][next_word] += 1
            self.first_order_totals[curr_word] += 1
        
        # Build second-order transition table
        for i in range(len(word_tokens) - 2):
            word1 = word_tokens[i]
            word2 = word_tokens[i + 1]
            next_word = word_tokens[i + 2]
            
            word_pair = (word1, word2)
            self.second_order_transitions[word_pair][next_word] += 1
            self.second_order_totals[word_pair] += 1
        
        self.is_trained = True
        
        # Log statistics
        elapsed = time.time() - start_time
        print(f"Training completed in {elapsed:.2f} seconds")
        print(f"First-order transitions: {len(self.first_order_transitions)}")
        print(f"Second-order transitions: {len(self.second_order_transitions)}")
    
    def predict_next_words(self, text, num_suggestions=3):
        """
        Predict the next possible words based on the input text.
        Uses second-order prediction when possible, falls back to first-order.
        
        Returns:
        - List of dictionaries with word and probability
        - Order of Markov Chain used (1 or 2)
        """
        if not self.is_trained:
            return [], 1
        
        # Clean and tokenize input text
        text = text.strip()
        if not text:
            return [], 1

        # Get the last sentence or phrase for prediction
        last_text = self._get_last_sentence_or_phrase(text)
        
        # Tokenize and filter to only words
        tokens = nltk.word_tokenize(last_text)
        word_tokens = [token.lower() for token in tokens if self._is_word(token)]
        
        # Try second-order prediction first (if we have at least two words)
        if len(word_tokens) >= 2:
            word1 = word_tokens[-2]
            word2 = word_tokens[-1]
            word_pair = (word1, word2)
            
            # Check if we have this pair in our model
            if word_pair in self.second_order_transitions and self.second_order_transitions[word_pair]:
                suggestions = self._get_top_suggestions(
                    self.second_order_transitions[word_pair],
                    self.second_order_totals[word_pair],
                    num_suggestions
                )
                return suggestions, 2
        
        # Fall back to first-order prediction
        if word_tokens:
            last_word = word_tokens[-1]
            
            # Check if we have this word in our model
            if last_word in self.first_order_transitions and self.first_order_transitions[last_word]:
                suggestions = self._get_top_suggestions(
                    self.first_order_transitions[last_word],
                    self.first_order_totals[last_word],
                    num_suggestions
                )
                return suggestions, 1
        
        # If we can't predict based on the last word, return the most common words overall
        all_next_words = Counter()
        for counter in self.first_order_transitions.values():
            all_next_words.update(counter)
        
        # Get top overall words as a last resort
        total_words = sum(all_next_words.values())
        
        if total_words > 0:
            suggestions = [
                {
                    "word": word,
                    "probability": round((count / total_words) * 100)
                }
                for word, count in all_next_words.most_common(num_suggestions)
            ]
            return suggestions, 1
        
        return [], 1
        
    def _get_last_sentence_or_phrase(self, text):
        """
        Get the last sentence or phrase (up to 10 words) for prediction context.
        """
        # Try to get the last sentence first
        sentences = text.split('.')
        last_sentence = sentences[-1].strip()
        
        if last_sentence:
            return last_sentence
            
        # If no clear sentence, get the last few words
        words = text.split()
        return ' '.join(words[-10:]) if words else ""
    
    def _get_top_suggestions(self, counter, total_count, num_suggestions):
        """
        Get the top N suggestions from a counter, with probabilities.
        Only returns valid words (no punctuation-only tokens).
        """
        suggestions = []
        
        # Get most common next words, filtering out non-words
        for word, count in counter.most_common():
            if self._is_word(word) and len(suggestions) < num_suggestions:
                probability = round((count / total_count) * 100)
                suggestions.append({
                    "word": word,
                    "probability": probability
                })
        
        return suggestions

    def load_sources_from_directory(self, directory_path):
        """
        Load all .txt files from a directory as sources.
        """
        if not os.path.exists(directory_path):
            return []
        
        loaded_sources = []
        
        for filename in os.listdir(directory_path):
            if filename.endswith('.txt'):
                try:
                    with open(os.path.join(directory_path, filename), 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Add as an active source
                    self.add_source(filename, content, active=True)
                    loaded_sources.append(filename)
                except Exception as e:
                    print(f"Error loading source {filename}: {str(e)}")
        
        return loaded_sources