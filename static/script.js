document.addEventListener('DOMContentLoaded', () => {
    const DOM = {
        textInput: document.getElementById('text-input'),
        suggestionsContainer: document.getElementById('suggestions-container'),
        sourceToggles: document.getElementById('source-toggles'),
        orderIndicator: document.getElementById('order-indicator'),
        loadingOverlay: document.getElementById('loading-overlay'),
        activeSources: document.getElementById('active-sources'),
        resetBtn: document.getElementById('reset-btn')
    };

    let timeout;
    let cursorPosition = 0;

    // Debounced prediction fetcher
    const fetchPredictionsDebounced = (text) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fetchPredictions(text), 300);
    };

    // Reset handler
    DOM.resetBtn.addEventListener('click', () => {
        DOM.textInput.value = '';
        cursorPosition = 0;
        updateSuggestions([], 1);
    });

    // Prediction logic
    const fetchPredictions = async (text) => {
        showLoading();
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            
            if (!response.ok) throw new Error('Prediction failed');
            const data = await response.json();
            
            updateSuggestions(data.suggestions, data.order);
            updateActiveSourcesCount();
        } catch (error) {
            console.error('Prediction error:', error);
            updateSuggestions([], 1);
        } finally {
            hideLoading();
        }
    };

    // Suggestion rendering
    const updateSuggestions = (suggestions, order) => {
        DOM.suggestionsContainer.innerHTML = suggestions.length > 0 
            ? suggestions.map(suggestion => `
                <button class="suggestion-chip flex items-center justify-center p-3 bg-white border border-gray-200 rounded-lg hover:border-indigo-200 transition-colors"
                        onclick="appendSuggestion('${suggestion.word}')">
                    <span class="font-medium">${suggestion.word}</span>
                    <span class="text-sm text-indigo-600 ml-2">${suggestion.probability}%</span>
                </button>
              `).join('')
            : `<div class="col-span-3 text-center py-2 text-gray-500">No suggestions available</div>`;

        DOM.orderIndicator.textContent = `${order === 2 ? '2nd' : '1st'} Order`;
        DOM.orderIndicator.className = `px-3 py-1 rounded-full text-sm font-medium ${
            order === 2 ? 'bg-indigo-100 text-indigo-700' : 'bg-purple-100 text-purple-700'
        }`;
    };

    // Text input handling
    DOM.textInput.addEventListener('input', (e) => {
        cursorPosition = e.target.selectionStart;
        fetchPredictionsDebounced(e.target.value);
    });

    // Source management
    const fetchSources = async () => {
        try {
            const response = await fetch('/sources');
            const { sources } = await response.json();
            renderSources(sources);
        } catch (error) {
            console.error('Error loading sources:', error);
            DOM.sourceToggles.innerHTML = '<p class="text-red-500">Error loading sources</p>';
        }
    };

    const renderSources = (sources) => {
        DOM.sourceToggles.innerHTML = sources.map(({ name, active }) => `
            <div class="flex items-center p-3 border border-gray-200 rounded-lg">
                <label class="flex items-center cursor-pointer">
                    <input type="checkbox" ${active ? 'checked' : ''} 
                           class="mr-3 h-5 w-5 accent-indigo-500"
                           onchange="toggleSource('${name}', this.checked)">
                    <span class="text-gray-700">${name}</span>
                </label>
            </div>
        `).join('');
    };

    // Helper functions
    const showLoading = () => DOM.loadingOverlay.classList.remove('hidden');
    const hideLoading = () => DOM.loadingOverlay.classList.add('hidden');
    const updateActiveSourcesCount = () => {
        const activeCount = document.querySelectorAll('#source-toggles input:checked').length;
        DOM.activeSources.textContent = `${activeCount} active`;
    };

    // Global functions
    window.appendSuggestion = (word) => {
        const text = DOM.textInput.value;
        const beforeCursor = text.slice(0, cursorPosition);
        const afterCursor = text.slice(cursorPosition);
        
        // Check if we need to add a space before the word
        // Add space if there's existing text and it doesn't end with whitespace
        const needsSpaceBefore = beforeCursor.length > 0 && !/\s$/.test(beforeCursor);
        
        // Build the word to insert with proper spacing
        let wordToInsert = '';
        if (needsSpaceBefore) {
            wordToInsert = ` ${word} `;
        } else {
            wordToInsert = `${word} `;
        }
        
        // Insert the word with proper spacing
        DOM.textInput.value = `${beforeCursor}${wordToInsert}${afterCursor}`;
        
        // Update cursor position to be after the inserted word and space
        cursorPosition = beforeCursor.length + wordToInsert.length;
        DOM.textInput.setSelectionRange(cursorPosition, cursorPosition);
        DOM.textInput.focus();
        
        fetchPredictionsDebounced(DOM.textInput.value);
    };

    window.toggleSource = async (source, active) => {
        showLoading();
        try {
            await fetch('/toggle_source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source, active })
            });
            await fetchPredictions(DOM.textInput.value);
            updateActiveSourcesCount();
        } finally {
            hideLoading();
        }
    };

    // Initial setup
    fetchSources();
    fetchPredictionsDebounced('');
});