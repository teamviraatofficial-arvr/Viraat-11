// Chat Module

const ChatModule = {
    init() {
        this.bindEvents();
        // Initialize Visualizer if available
        if (window.VisualizerModule) {
            window.VisualizerModule.init();
        }
    },
    
    bindEvents() {
        // New chat button
        document.getElementById('newChatBtn')?.addEventListener('click', () => {
            this.createNewConversation();
        });
        
        // Send button
        document.getElementById('sendBtn')?.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key to send (Shift+Enter for new line)
        document.getElementById('messageInput')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        document.getElementById('messageInput')?.addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
            
            // Enable/disable send button
            document.getElementById('sendBtn').disabled = !e.target.value.trim();
        });
        
        // Example queries
        document.querySelectorAll('.example-query').forEach(el => {
            el.addEventListener('click', (e) => {
                const query = e.target.dataset.query;
                document.getElementById('messageInput').value = query;
                this.sendMessage();
            });
        });
        
        // RAG toggle
        document.getElementById('ragToggleBtn')?.addEventListener('click', (e) => {
            window.appState.useRAG = !window.appState.useRAG;
            e.currentTarget.classList.toggle('active', window.appState.useRAG);
        });
        
        // Analytics button
        document.getElementById('viewAnalyticsBtn')?.addEventListener('click', () => {
            this.showAnalytics();
        });
        
        document.getElementById('closeAnalyticsBtn')?.addEventListener('click', () => {
            document.getElementById('analyticsModal').classList.remove('active');
        });
    },
    
    async loadConversations() {
        try {
            const conversations = await window.api.request('/api/v1/conversations');
            window.appState.conversations = conversations;
            this.renderConversations();
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    },
    
    renderConversations() {
        const list = document.getElementById('conversationsList');
        if (!list) return;
        list.innerHTML = '';
        
        window.appState.conversations.forEach(conv => {
            const el = document.createElement('div');
            el.className = 'conversation-item';
            if (window.appState.currentConversation?.id === conv.id) {
                el.classList.add('active');
            }
            
            el.innerHTML = `
                <div class="conversation-header">
                    <div class="conversation-title" title="${conv.title}">${conv.title}</div>
                    <div class="conversation-actions">
                        <button class="btn-action-small edit" title="Rename" onclick="window.ChatModule.renameConversation(${conv.id})">✏️</button>
                        <button class="btn-action-small delete" title="Delete" onclick="window.ChatModule.deleteConversation(${conv.id}, event)">🗑️</button>
                    </div>
                </div>
                <div class="conversation-time">${new Date(conv.updated_at).toLocaleDateString()}</div>
            `;
            
            // Allow click on item to load, but prevent actions from triggering load
            el.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-action-small')) {
                    this.loadConversation(conv.id);
                }
            });
            
            list.appendChild(el);
        });
    },

    async deleteConversation(id, event) {
        if (event) event.stopPropagation();
        if (!confirm('Are you sure you want to delete this conversation?')) return;
        
        try {
            await window.api.request(`/api/v1/conversations/${id}`, { method: 'DELETE' });
            
            // If deleting current, clear view
            if (window.appState.currentConversation?.id === id) {
                window.appState.currentConversation = null;
                document.getElementById('messagesContainer').innerHTML = '';
                document.getElementById('chatContainer').classList.add('hidden');
                document.getElementById('welcomeScreen').classList.remove('hidden');
            }
            
            this.loadConversations();
        } catch (error) {
            console.error('Delete failed:', error);
            window.utils.showNotification('Failed to delete conversation', 'error');
        }
    },

    async renameConversation(id, currentTitle) {
        const newTitle = prompt("Enter new conversation title:", currentTitle || "");
        if (!newTitle) return;
        
        try {
            await window.api.request(`/api/v1/conversations/${id}`, {
                method: 'PATCH',
                body: JSON.stringify({ title: newTitle })
            });
            this.loadConversations();
            
            // Update title if current
            if (window.appState.currentConversation?.id === id) {
                document.getElementById('currentConversationTitle').textContent = newTitle;
            }
        } catch (error) {
            console.error('Rename failed:', error);
            window.utils.showNotification('Failed to rename conversation', 'error');
        }
    },
    
    async createNewConversation() {
        try {
            const response = await window.api.request('/api/v1/conversations', {
                method: 'POST',
                body: JSON.stringify({ title: `New Conversation` })
            });
            
            window.appState.currentConversation = response;
            
            // Clear messages
            document.getElementById('messagesContainer').innerHTML = '';
            document.getElementById('welcomeScreen').classList.add('hidden');
            document.getElementById('chatContainer').classList.remove('hidden');
            document.getElementById('currentConversationTitle').textContent = response.title;
            
            // Reload conversations list
            this.loadConversations();
            return response;
        } catch (error) {
            console.error('Failed to create conversation:', error);
            window.utils.showNotification('Failed to create conversation', 'error');
            return null;
        }
    },
    
    async loadConversation(conversationId) {
        try {
            const messages = await window.api.request(`/api/v1/conversations/${conversationId}/messages`);
            
            window.appState.currentConversation = { id: conversationId };
            
            // Show chat container
            document.getElementById('welcomeScreen').classList.add('hidden');
            document.getElementById('chatContainer').classList.remove('hidden');
            
            // Render messages
            this.renderMessages(messages);
            this.renderConversations();
        } catch (error) {
            window.utils.showNotification('Failed to load conversation', 'error');
        }
    },
    
    renderMessages(messages) {
        const container = document.getElementById('messagesContainer');
        if (!container) return;
        container.innerHTML = '';
        
        messages.forEach(msg => {
            this.addMessageToUI(msg.role, msg.content, msg.created_at);
        });
        
        container.scrollTop = container.scrollHeight;
    },
    
    addMessageToUI(role, content, timestamp) {
        const container = document.getElementById('messagesContainer');
        if (!container) return;
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const displayRole = role.charAt(0).toUpperCase() + role.slice(1);
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        // Convert markdown to HTML
        const htmlContent = window.marked ? marked.parse(content) : content;
        
        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-role">${displayRole}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${htmlContent}</div>
            </div>
        `;
        
        container.appendChild(messageEl);
        
        // Highlight code blocks
        if (window.Prism) {
            messageEl.querySelectorAll('pre code').forEach((block) => {
                Prism.highlightElement(block);
            });
        }
        
        container.scrollTop = container.scrollHeight;
    },
    
    showTypingIndicator() {
        const container = document.getElementById('messagesContainer');
        if (!container) return;
        const typingEl = document.createElement('div');
        typingEl.id = 'typingIndicator';
        typingEl.className = 'message assistant';
        
        typingEl.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        container.appendChild(typingEl);
        container.scrollTop = container.scrollHeight;
    },
    
    removeTypingIndicator() {
        const typingEl = document.getElementById('typingIndicator');
        if (typingEl) {
            typingEl.remove();
        }
    },
    
    async sendMessage() {
        const input = document.getElementById('messageInput');
        if (!input) return;
        const query = input.value.trim();
        
        if (!query) return;
        
        // Show chat container if hidden
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('chatContainer').classList.remove('hidden');
        
        // Show typing indicator
        this.showTypingIndicator();

        // Create conversation if needed
        if (!window.appState.currentConversation) {
            const success = await this.createNewConversation();
            if (!success) {
                this.removeTypingIndicator();
                return;
            }
        }
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('sendBtn').disabled = true;
        
        // Add user message
        this.addMessageToUI('user', query);
        
        try {
            if (!window.appState.currentConversation || !window.appState.currentConversation.id) {
                throw new Error("Conversation not properly initialized.");
            }

            const response = await window.api.request('/api/v1/chat', {
                method: 'POST',
                body: JSON.stringify({
                    query,
                    conversation_id: window.appState.currentConversation.id,
                    use_rag: window.appState.useRAG
                })
            });
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add assistant response
            // Robust parsing for Visual Directive
            let displayText = response.response;
            const marker = '[VISUAL_DIRECTIVE:';
            const markerIndex = displayText.indexOf(marker);
            
            if (markerIndex !== -1) {
                // Found the marker
                const directiveStart = markerIndex + marker.length;
                const directiveEnd = displayText.lastIndexOf(']'); // Assuming it's at the end
                
                if (directiveEnd > directiveStart) {
                    const jsonStr = displayText.substring(directiveStart, directiveEnd);
                    
                    // Remove the entire block from visible text including marker and brackets
                    // We remove from markerIndex to the end (or specific closing bracket if we want to be safe)
                    // But usually the directive is appended at the end.
                    displayText = displayText.substring(0, markerIndex).trim();
                    
                    if (window.VisualizerModule) {
                        try {
                            const directive = JSON.parse(jsonStr);
                            console.log("Visual Directive Found:", directive);
                            // Delay slightly to ensure UI update
                            setTimeout(() => {
                                window.VisualizerModule.loadModel(directive.model_id, directive.model_name);
                            }, 100);
                        } catch (e) {
                            console.error("Failed to parse visual directive JSON", e);
                            console.log("Raw JSON string:", jsonStr);
                        }
                    }
                }
            }
            
            this.addMessageToUI('assistant', displayText);
            
            // Update conversation in list
            // Update conversation in list
            this.loadConversations();

            // Auto-title if it's a new conversation (heuristic)
            if (window.appState.currentConversation && 
                (window.appState.currentConversation.title === 'New Conversation' || 
                 window.appState.currentConversation.title.startsWith("Conversation 20"))) {
                
                const newTitle = query.length > 30 ? query.substring(0, 30) + '...' : query;
                // Silent rename
                window.api.request(`/api/v1/conversations/${window.appState.currentConversation.id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ title: newTitle })
                }).then(() => {
                    this.loadConversations();
                    document.getElementById('currentConversationTitle').textContent = newTitle;
                }).catch(e => console.error("Auto-title failed", e));
            }
            
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToUI('assistant', `Error: ${error.message}`);
            window.utils.showNotification('Failed to get response', 'error');
        }
    },
    
    async showAnalytics() {
        const modal = document.getElementById('analyticsModal');
        const content = document.getElementById('analyticsContent');
        if (!modal || !content) return;
        
        modal.classList.add('active');
        content.innerHTML = '<p>Loading analytics...</p>';
        
        try {
            const stats = await window.api.request('/api/v1/analytics/dashboard');
            
            content.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${stats.total_queries}</div>
                        <div class="stat-label">Total Queries</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.average_response_time}s</div>
                        <div class="stat-label">Avg Response Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.rag_stats.queries_with_rag}</div>
                        <div class="stat-label">RAG Queries</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.rag_stats.average_sources}</div>
                        <div class="stat-label">Avg Sources Used</div>
                    </div>
                </div>
                
                <h3 style="margin: 2rem 0 1rem; color: var(--primary);">Popular Queries</h3>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    ${stats.popular_queries.map(q => `
                        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px;">
                            <div style="font-weight: 500;">${q[0] || 'Unknown'}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted);">Asked ${q[1]} times</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch (error) {
            content.innerHTML = '<p>Failed to load analytics</p>';
        }
    }
};

// Initialize after DOM and Auth
document.addEventListener('DOMContentLoaded', () => {
    ChatModule.init();
});

window.ChatModule = ChatModule;
