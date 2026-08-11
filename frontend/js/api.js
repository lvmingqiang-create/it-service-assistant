/**
 * API Client Module
 * =================
 * Wraps all backend API calls into simple functions.
 * Centralizes the base URL and error handling.
 */

// API base URL - adjust if backend runs on different host/port
const API_BASE = 'http://localhost:8000/api';

/**
 * Generic fetch wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ============ Chat API ============

const ChatAPI = {
    /**
     * Send a chat message and get a reply
     * @param {Array} messages - Array of {role, content}
     * @param {string} sessionId - Optional session ID
     */
    async send(messages, sessionId = null) {
        return apiRequest('/chat/send', {
            method: 'POST',
            body: JSON.stringify({ messages, session_id: sessionId }),
        });
    },
    
    /**
     * Get current LLM model info
     */
    async getModels() {
        return apiRequest('/models');
    },
};

// ============ RAG API ============

const RAGAPI = {
    /**
     * Ask a question using RAG
     * @param {string} question - User question
     * @param {Array} history - Optional chat history
     */
    async query(question, history = null) {
        return apiRequest('/rag/query', {
            method: 'POST',
            body: JSON.stringify({ question, history }),
        });
    },
    
    /**
     * Pure semantic search
     * @param {string} query - Search query
     */
    async search(query) {
        return apiRequest('/rag/search', {
            method: 'POST',
            body: JSON.stringify({ question: query }),
        });
    },
};

// ============ Agent API ============

const AgentAPI = {
    /**
     * Run agent query
     * @param {string} query - User question/task
     * @param {boolean} showThinking - Whether to return thinking process
     */
    async run(query, showThinking = true) {
        return apiRequest('/agent/run', {
            method: 'POST',
            body: JSON.stringify({ query, show_thinking: showThinking }),
        });
    },
    
    /**
     * Get list of available tools
     */
    async getTools() {
        return apiRequest('/agent/tools');
    },
    
    /**
     * Get all mock tickets
     */
    async getTickets() {
        return apiRequest('/agent/tickets');
    },
};

// ============ Documents API ============

const DocumentsAPI = {
    /**
     * Upload a document file
     * @param {File} file - File object
     */
    async upload(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const url = `${API_BASE}/documents/upload`;
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
        }
        
        return response.json();
    },
    
    /**
     * List all documents
     */
    async list() {
        return apiRequest('/documents');
    },
    
    /**
     * Delete a document
     * @param {string} docId - Document ID
     */
    async delete(docId) {
        return apiRequest(`/documents/${docId}`, {
            method: 'DELETE',
        });
    },
    
    /**
     * Index a document into vector DB
     * @param {string} docId - Document ID
     */
    async index(docId) {
        return apiRequest(`/documents/${docId}/index`, {
            method: 'POST',
        });
    },
};

// ============ Admin API ============

const AdminAPI = {
    /**
     * Get knowledge base statistics
     */
    async getStats() {
        return apiRequest('/admin/stats');
    },
    
    /**
     * Get detailed health check
     */
    async getHealth() {
        return apiRequest('/admin/health');
    },
    
    /**
     * Clear entire knowledge base
     */
    async clearKB() {
        return apiRequest('/admin/clear-kb', {
            method: 'POST',
        });
    },
};
