// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State management
const state = {
    user: null,
    token: null,
    currentConversation: null,
    conversations: [],
    useRAG: true,
    voiceEnabled: false
};

// Save/load state from localStorage
function saveState() {
    localStorage.setItem('viraat_token', state.token || '');
    localStorage.setItem('viraat_user', JSON.stringify(state.user || {}));
}

function loadState() {
    const token = localStorage.getItem('viraat_token');
    const user = localStorage.getItem('viraat_user');
    
    if (token && user) {
        state.token = token;
        state.user = JSON.parse(user);
        return true;
    }
    return false;
}

function clearState() {
    state.user = null;
    state.token = null;
    state.currentConversation = null;
    state.conversations = [];
    localStorage.removeItem('viraat_token');
    localStorage.removeItem('viraat_user');
}

// API helper functions
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Show/hide loading
function showLoading() {
    document.getElementById('loadingIndicator').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingIndicator').classList.add('hidden');
}

// Show notifications
function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Could be enhanced with toast notifications
}

// Export state and functions
window.appState = state;
window.api = {
    request: apiRequest,
    baseUrl: API_BASE_URL
};
window.utils = {
    showLoading,
    hideLoading,
    showNotification,
    saveState,
    loadState,
    clearState
};
