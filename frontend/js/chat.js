/**
 * Chat Interface Logic
 * =====================
 * Handles the main chat page interaction, including:
 * - Mode switching (chat / rag / agent)
 * - Message display and scrolling
 * - Sending messages and rendering responses
 * - Thinking process display (agent mode)
 */

// Application state
let currentMode = 'chat'; // 'chat' | 'rag' | 'agent' | 'ops-agent' | 'multi-agent'
let conversationHistory = [];
let agentHistory = []; // Persistent history for Agent mode only (max 10 messages)
let opsAgentHistory = []; // Persistent history for Operations Agent mode (max 10 messages)
let multiAgentHistory = []; // Persistent history for Multi-Agent mode (max 10 messages)
let isLoading = false;

// ============ Agent History Persistence ============

const AGENT_HISTORY_KEY = 'agent_conversation_history';
const OPS_AGENT_HISTORY_KEY = 'ops_agent_conversation_history';
const MULTI_AGENT_HISTORY_KEY = 'multi_agent_conversation_history';
const MAX_AGENT_HISTORY = 10;

function loadAgentHistory() {
    try {
        const stored = localStorage.getItem(AGENT_HISTORY_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.warn('Failed to load agent history:', e);
        return [];
    }
}

function saveAgentHistory() {
    try {
        const trimmed = agentHistory.slice(-MAX_AGENT_HISTORY);
        localStorage.setItem(AGENT_HISTORY_KEY, JSON.stringify(trimmed));
    } catch (e) {
        console.warn('Failed to save agent history:', e);
    }
}

function clearAgentHistory() {
    try {
        localStorage.removeItem(AGENT_HISTORY_KEY);
    } catch (e) {
        console.warn('Failed to clear agent history:', e);
    }
}

// ============ Operations Agent History Persistence ============

function loadOpsAgentHistory() {
    try {
        const stored = localStorage.getItem(OPS_AGENT_HISTORY_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.warn('Failed to load ops agent history:', e);
        return [];
    }
}

function saveOpsAgentHistory() {
    try {
        const trimmed = opsAgentHistory.slice(-MAX_AGENT_HISTORY);
        localStorage.setItem(OPS_AGENT_HISTORY_KEY, JSON.stringify(trimmed));
    } catch (e) {
        console.warn('Failed to save ops agent history:', e);
    }
}

function clearOpsAgentHistory() {
    try {
        localStorage.removeItem(OPS_AGENT_HISTORY_KEY);
    } catch (e) {
        console.warn('Failed to clear ops agent history:', e);
    }
}

// ============ Multi-Agent History Persistence ============

function loadMultiAgentHistory() {
    try {
        const stored = localStorage.getItem(MULTI_AGENT_HISTORY_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.warn('Failed to load multi-agent history:', e);
        return [];
    }
}

function saveMultiAgentHistory() {
    try {
        const trimmed = multiAgentHistory.slice(-MAX_AGENT_HISTORY);
        localStorage.setItem(MULTI_AGENT_HISTORY_KEY, JSON.stringify(trimmed));
    } catch (e) {
        console.warn('Failed to save multi-agent history:', e);
    }
}

function clearMultiAgentHistory() {
    try {
        localStorage.removeItem(MULTI_AGENT_HISTORY_KEY);
    } catch (e) {
        console.warn('Failed to clear multi-agent history:', e);
    }
}

// Mode metadata
const MODES = {
    chat: {
        title: 'Chat',
        subtitle: 'Direct AI conversation for general questions',
        icon: '💬',
    },
    rag: {
        title: 'Knowledge Base',
        subtitle: 'Answer questions based on IT knowledge base with source citations',
        icon: '📚',
    },
    agent: {
        title: 'Smart Agent',
        subtitle: 'AI autonomously invokes tools (knowledge base/tickets/FAQ) to solve complex issues',
        icon: '🧠',
    },
    'ops-agent': {
        title: 'Operations Agent',
        subtitle: 'IT operations tasks: system status, service management, logs, resource monitoring',
        icon: '🔧',
    },
    'multi-agent': {
        title: 'Multi-Agent',
        subtitle: 'Router Agent classifies and dispatches to Service or Operations Agent',
        icon: '🌐',
    },
};

// ============ Mode Switching ============

function setMode(mode) {
    currentMode = mode;
    const modeInfo = MODES[mode];
    
    // Update header
    document.getElementById('chat-title').textContent = modeInfo.title;
    document.getElementById('chat-subtitle').textContent = modeInfo.subtitle;
    document.getElementById('current-mode').textContent = modeInfo.title;
    
    // Update sidebar buttons
    ['chat', 'rag', 'agent', 'ops-agent', 'multi-agent'].forEach(m => {
        const btn = document.getElementById(`btn-mode-${m}`);
        if (btn) {
            if (m === mode) {
                btn.classList.add('bg-gray-700');
                btn.classList.remove('hover:bg-gray-700');
            } else {
                btn.classList.remove('bg-gray-700');
                btn.classList.add('hover:bg-gray-700');
            }
        }
    });
    
    // Show/hide thinking toggle (show for all agent modes)
    const thinkingToggle = document.getElementById('thinking-toggle-container');
    thinkingToggle.style.display = (mode === 'agent' || mode === 'ops-agent' || mode === 'multi-agent') ? 'flex' : 'none';
    
    // Load history BEFORE clearing chat
    if (mode === 'agent') {
        agentHistory = loadAgentHistory();
    } else if (mode === 'ops-agent') {
        opsAgentHistory = loadOpsAgentHistory();
    } else if (mode === 'multi-agent') {
        multiAgentHistory = loadMultiAgentHistory();
    }
    
    // Clear visual chat history when switching modes
    clearChat();
    
    // Restore history messages to UI if in agent mode
    if (mode === 'agent' && agentHistory.length > 0) {
        restoreAgentHistoryToUI();
    } else if (mode === 'ops-agent' && opsAgentHistory.length > 0) {
        restoreOpsAgentHistoryToUI();
    } else if (mode === 'multi-agent' && multiAgentHistory.length > 0) {
        restoreMultiAgentHistoryToUI();
    }
}

function restoreAgentHistoryToUI() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    
    agentHistory.forEach(msg => {
        if (msg.role === 'user') {
            addUserMessage(msg.content);
        } else if (msg.role === 'assistant') {
            addAssistantMessage(msg.content);
        }
    });
    
    scrollToBottom();
}

function restoreOpsAgentHistoryToUI() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    
    opsAgentHistory.forEach(msg => {
        if (msg.role === 'user') {
            addUserMessage(msg.content);
        } else if (msg.role === 'assistant') {
            addAssistantMessage(msg.content);
        }
    });
    
    scrollToBottom();
}

function restoreMultiAgentHistoryToUI() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    
    multiAgentHistory.forEach(msg => {
        if (msg.role === 'user') {
            addUserMessage(msg.content);
        } else if (msg.role === 'assistant') {
            addAssistantMessage(msg.content);
        }
    });
    
    scrollToBottom();
}

// ============ Message Rendering ============

function addUserMessage(content) {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'flex justify-end message-fade-in';
    msgDiv.innerHTML = `
        <div class="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-xl">
            <p class="whitespace-pre-wrap text-sm">${escapeHtml(content)}</p>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function addAssistantMessage(content, sources = null) {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'flex justify-start message-fade-in';
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="mt-3 pt-3 border-t border-gray-200">
                <div class="text-xs text-gray-500 mb-1">📎 Sources:</div>
                <div class="flex flex-wrap gap-1">
                    ${sources.map(s => `<span class="source-tag">${escapeHtml(s.source)}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    msgDiv.innerHTML = `
        <div class="flex gap-3 max-w-2xl">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 text-sm">
                🤖
            </div>
            <div class="bg-white border rounded-2xl rounded-tl-sm px-4 py-3">
                <div class="text-sm text-gray-800 whitespace-pre-wrap">${formatMarkdown(content)}</div>
                ${sourcesHtml}
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function addThinkingSteps(steps) {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'flex justify-start message-fade-in';
    
    let stepsHtml = steps.map(step => {
        const labels = {
            thought: '💭 Thought',
            action: '⚡ Action',
            observation: '👁️ Observation',
        };
        const label = labels[step.step_type] || step.step_type;
        return `
            <div class="thinking-step ${step.step_type}">
                <span class="font-medium">${label}</span>
                ${step.tool ? `<span class="ml-2 text-xs">[${escapeHtml(step.tool)}]</span>` : ''}
                <div class="mt-1">${escapeHtml(step.content)}</div>
            </div>
        `;
    }).join('');
    
    msgDiv.innerHTML = `
        <div class="flex gap-3 max-w-2xl">
            <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0 text-sm">
                🧠
            </div>
            <div class="bg-amber-50 border border-amber-200 rounded-2xl rounded-tl-sm px-4 py-3 flex-1">
                <div class="text-xs text-amber-700 font-medium mb-2">Agent Thinking Process</div>
                ${stepsHtml}
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.id = 'loading-message';
    msgDiv.className = 'flex justify-start message-fade-in';
    msgDiv.innerHTML = `
        <div class="flex gap-3">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 text-sm">
                🤖
            </div>
            <div class="bg-white border rounded-2xl rounded-tl-sm px-4 py-3">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function removeLoadingMessage() {
    const loading = document.getElementById('loading-message');
    if (loading) loading.remove();
}

// ============ Send Message ============

async function sendMessage() {
    const input = document.getElementById('user-input');
    const content = input.value.trim();
    
    if (!content || isLoading) return;
    
    isLoading = true;
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    sendBtn.classList.add('opacity-50');
    
    // Add user message
    addUserMessage(content);
    input.value = '';
    
    // Add to history
    conversationHistory.push({ role: 'user', content });
    
    // Show loading
    addLoadingMessage();
    
    try {
        let response;
        
        if (currentMode === 'chat') {
            // Direct chat mode
            response = await ChatAPI.send(conversationHistory);
            removeLoadingMessage();
            addAssistantMessage(response.reply);
            conversationHistory.push({ role: 'assistant', content: response.reply });
            
        } else if (currentMode === 'rag') {
            // RAG mode
            response = await RAGAPI.query(content);
            removeLoadingMessage();
            addAssistantMessage(response.answer, response.sources);
            
        } else if (currentMode === 'agent') {
            // Agent mode
            const showThinking = document.getElementById('show-thinking').checked;
            
            // Add to agent history
            agentHistory.push({ role: 'user', content });
            saveAgentHistory();
            
            // Pass last 10 messages as history
            const historyToSend = agentHistory.slice(-MAX_AGENT_HISTORY);
            response = await AgentAPI.run(content, showThinking, historyToSend);
            
            removeLoadingMessage();
            
            // Show thinking steps first (if enabled)
            if (showThinking && response.steps && response.steps.length > 0) {
                addThinkingSteps(response.steps);
            }
            
            // Show final answer
            addAssistantMessage(response.answer);
            
            // Add assistant response to agent history
            agentHistory.push({ role: 'assistant', content: response.answer });
            saveAgentHistory();
            
            // Show tools used
            if (response.tools_used && response.tools_used.length > 0) {
                const messagesDiv = document.getElementById('messages');
                const toolsDiv = document.createElement('div');
                toolsDiv.className = 'flex justify-start message-fade-in pl-11';
                toolsDiv.innerHTML = `
                    <div class="text-xs text-gray-400">
                        Tools used: ${response.tools_used.join(' → ')}
                    </div>
                `;
                messagesDiv.appendChild(toolsDiv);
                scrollToBottom();
            }
            
        } else if (currentMode === 'ops-agent') {
            // Operations Agent mode
            const showThinking = document.getElementById('show-thinking').checked;
            
            // Add to ops agent history
            opsAgentHistory.push({ role: 'user', content });
            saveOpsAgentHistory();
            
            // Pass last 10 messages as history
            const historyToSend = opsAgentHistory.slice(-MAX_AGENT_HISTORY);
            response = await OperationsAgentAPI.run(content, showThinking, historyToSend);
            
            removeLoadingMessage();
            
            // Show thinking steps first (if enabled)
            if (showThinking && response.steps && response.steps.length > 0) {
                addThinkingSteps(response.steps);
            }
            
            // Show final answer
            addAssistantMessage(response.answer);
            
            // Add assistant response to ops agent history
            opsAgentHistory.push({ role: 'assistant', content: response.answer });
            saveOpsAgentHistory();
            
            // Show tools used
            if (response.tools_used && response.tools_used.length > 0) {
                const messagesDiv = document.getElementById('messages');
                const toolsDiv = document.createElement('div');
                toolsDiv.className = 'flex justify-start message-fade-in pl-11';
                toolsDiv.innerHTML = `
                    <div class="text-xs text-gray-400">
                        Tools used: ${response.tools_used.join(' → ')}
                    </div>
                `;
                messagesDiv.appendChild(toolsDiv);
                scrollToBottom();
            }
            
        } else if (currentMode === 'multi-agent') {
            // Multi-Agent mode
            const showThinking = document.getElementById('show-thinking').checked;
            
            // Add to multi-agent history
            multiAgentHistory.push({ role: 'user', content });
            saveMultiAgentHistory();
            
            // Pass last 10 messages as history
            const historyToSend = multiAgentHistory.slice(-MAX_AGENT_HISTORY);
            response = await MultiAgentAPI.run(content, showThinking, historyToSend);
            
            removeLoadingMessage();
            
            // Show routing info
            const messagesDiv = document.getElementById('messages');
            const routingDiv = document.createElement('div');
            routingDiv.className = 'flex justify-start message-fade-in pl-11';
            routingDiv.innerHTML = `
                <div class="text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2 mb-2">
                    <span class="font-semibold">Router:</span> Routed to <span class="text-blue-600 font-semibold">${response.target === 'service' ? 'Smart Agent' : 'Operations Agent'}</span> (confidence: ${(response.confidence * 100).toFixed(0)}%)<br>
                    <span class="text-gray-500">${response.reason}</span>
                </div>
            `;
            messagesDiv.appendChild(routingDiv);
            
            // Show thinking steps first (if enabled)
            if (showThinking && response.thinking_process && response.thinking_process.length > 0) {
                addThinkingSteps(response.thinking_process);
            }
            
            // Show final answer
            addAssistantMessage(response.answer);
            
            // Add assistant response to multi-agent history
            multiAgentHistory.push({ role: 'assistant', content: response.answer });
            saveMultiAgentHistory();
            
            scrollToBottom();
        }
        
    } catch (error) {
        removeLoadingMessage();
        addAssistantMessage(`❌ Error: ${error.message}\n\nPlease check if the backend service is running.`);
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        sendBtn.classList.remove('opacity-50');
        input.focus();
    }
}

// ============ Utility Functions ============

function clearChat(clearHistory = false) {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = `
        <div class="flex justify-center">
            <div class="text-gray-400 text-sm py-8">
                ${MODES[currentMode].icon} ${MODES[currentMode].title} Mode — Enter a question to start the conversation
            </div>
        </div>
    `;
    conversationHistory = [];
    
    // Only clear persistent history when clearHistory=true (user clicked "Clear Chat" button)
    // When switching modes (clearHistory=false), we preserve history in localStorage
    if (clearHistory) {
        if (currentMode === 'agent') {
            agentHistory = [];
            clearAgentHistory();
        } else if (currentMode === 'ops-agent') {
            opsAgentHistory = [];
            clearOpsAgentHistory();
        } else if (currentMode === 'multi-agent') {
            multiAgentHistory = [];
            clearMultiAgentHistory();
        }
    }
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // Very simple markdown formatting - just handle basic stuff
    let html = escapeHtml(text);
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Code inline
    html = html.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setMode('chat');
    document.getElementById('user-input').focus();
});