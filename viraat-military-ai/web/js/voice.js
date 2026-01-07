// Voice Module using Web Speech API

const VoiceModule = {
    recognition: null,
    synthesis: window.speechSynthesis,
    isListening: false,
    
    init() {
        // Check if browser supports Web Speech API
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.setupRecognition();
            this.bindEvents();
        } else {
            console.warn('Speech recognition not supported in this browser');
        }
    },
    
    setupRecognition() {
        if (!this.recognition) return;
        
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.addEventListener('result', (event) => {
            const transcript = event.results[0][0].transcript;
            const input = document.getElementById('messageInput');
            input.value = transcript;
            document.getElementById('sendBtn').disabled = false;
            window.utils.showNotification(`Recognized: "${transcript}"`, 'info');
        });
        
        this.recognition.addEventListener('end', () => {
            this.isListening = false;
            this.updateVoiceButton();
        });
        
        this.recognition.addEventListener('error', (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateVoiceButton();
            window.utils.showNotification('Voice recognition error', 'error');
        });
    },
    
    bindEvents() {
        const voiceBtn = document.getElementById('voiceToggleBtn');
        if (voiceBtn && this.recognition) {
            voiceBtn.addEventListener('click', () => {
                this.toggleVoiceInput();
            });
        }
    },
    
    toggleVoiceInput() {
        if (!this.recognition) {
            window.utils.showNotification('Voice input not supported', 'error');
            return;
        }
        
        if (this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        } else {
            this.recognition.start();
            this.isListening = true;
            window.utils.showNotification('Listening...', 'info');
        }
        
        this.updateVoiceButton();
    },
    
    updateVoiceButton() {
        const btn = document.getElementById('voiceToggleBtn');
        if (btn) {
            btn.classList.toggle('active', this.isListening);
            btn.textContent = this.isListening ? '🔴' : '🎤';
        }
    },
    
    speak(text) {
        if (!this.synthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        this.synthesis.speak(utterance);
    },
    
    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
    }
};

// Initialize after DOM load
document.addEventListener('DOMContentLoaded', () => {
    VoiceModule.init();
});

window.VoiceModule = VoiceModule;
