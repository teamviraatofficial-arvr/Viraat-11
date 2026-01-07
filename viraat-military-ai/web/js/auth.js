// Authentication Module

const AuthModule = {
    async init() {
        this.bindEvents();
        
        // Check if user is already logged in
        if (window.utils.loadState()) {
            this.showMainApp();
        } else {
            this.showAuthModal();
        }
    },
    
    bindEvents() {
        // Tab switching
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
        
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Register form
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
        
        // Guest Access
        document.getElementById('guestBtn')?.addEventListener('click', () => {
            this.handleGuestLogin();
        });
        
        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.handleLogout();
        });
    },
    
    async handleGuestLogin() {
        console.log('Continuing as guest...');
        window.appState.token = 'guest_token_mock';
        window.appState.user = {
            username: 'guest_warrior',
            full_name: 'Guest Personnel',
            role: 'guest'
        };
        window.utils.saveState();
        this.showMainApp();
        window.utils.showNotification('Welcome, Guest Personnel', 'info');
    },
    
    switchTab(tabName) {
        // Update tabs
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update forms
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tabName}Form`);
        });
    },
    
    async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        window.utils.showLoading();
        
        try {
            const response = await window.api.request('/api/v1/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            window.appState.token = response.access_token;
            window.appState.user = response.user;
            window.utils.saveState();
            
            this.showMainApp();
            window.utils.showNotification('Login successful!', 'success');
        } catch (error) {
            window.utils.showNotification(error.message, 'error');
        } finally {
            window.utils.hideLoading();
        }
    },
    
    async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const fullName = document.getElementById('registerFullName').value;
        
        window.utils.showLoading();
        
        try {
            const response = await window.api.request('/api/v1/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    full_name: fullName || null
                })
            });
            
            window.appState.token = response.access_token;
            window.appState.user = response.user;
            window.utils.saveState();
            
            this.showMainApp();
            window.utils.showNotification('Account created successfully!', 'success');
        } catch (error) {
            window.utils.showNotification(error.message, 'error');
        } finally {
            window.utils.hideLoading();
        }
    },
    
    handleLogout() {
        window.utils.clearState();
        this.showAuthModal();
        window.utils.showNotification('Logged out successfully', 'success');
    },
    
    showAuthModal() {
        document.getElementById('authModal').classList.add('active');
        document.getElementById('mainApp').classList.add('hidden');
    },
    
    showMainApp() {
        document.getElementById('authModal').classList.remove('active');
        document.getElementById('mainApp').classList.remove('hidden');
        
        // Update user info
        if (window.appState.user) {
            document.getElementById('userName').textContent = 
                window.appState.user.full_name || window.appState.user.username;
            document.getElementById('userRole').textContent = window.appState.user.role;
        }
        
        // Load conversations
        if (window.ChatModule) {
            window.ChatModule.loadConversations();
        }
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    AuthModule.init();
});

window.AuthModule = AuthModule;
