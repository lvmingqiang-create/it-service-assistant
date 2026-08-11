/**
 * Admin Page Logic
 * =================
 * Handles the admin page: document upload, document list,
 * indexing, stats display, and ticket list.
 */

// ============ Initialization ============

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadDocuments();
    loadTickets();
    setupDragAndDrop();
    setupFileInput();
});

// ============ Stats ============

async function loadStats() {
    try {
        const stats = await AdminAPI.getStats();
        document.getElementById('stat-documents').textContent = stats.total_documents;
        document.getElementById('stat-chunks').textContent = stats.total_chunks;
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('stat-documents').textContent = 'Error';
        document.getElementById('stat-chunks').textContent = 'Error';
    }
}

// ============ Document Management ============

async function loadDocuments() {
    const listDiv = document.getElementById('document-list');
    
    try {
        const result = await DocumentsAPI.list();
        const docs = result.documents;
        
        if (docs.length === 0) {
            listDiv.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                        No documents yet, upload your first document to get started
                    </div>
            `;
            return;
        }
        
        listDiv.innerHTML = docs.map(doc => `
            <div class="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <div class="font-medium text-sm text-gray-800 truncate" title="${escapeHtml(doc.filename)}">
                            📄 ${escapeHtml(doc.filename)}
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                            ${formatFileSize(doc.size)} · ${doc.upload_time}
                        </div>
                    </div>
                </div>
                <div class="flex gap-2 mt-2">
                    <button onclick="indexDocument('${doc.doc_id}')" 
                            class="flex-1 px-2 py-1 text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 rounded">
                        Vectorize
                    </button>
                    <button onclick="deleteDocument('${doc.doc_id}')" 
                            class="px-2 py-1 text-xs bg-red-50 text-red-600 hover:bg-red-100 rounded">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        listDiv.innerHTML = `
            <div class="text-center text-red-400 py-8">
                Load failed: ${error.message}
            </div>
        `;
    }
}

async function uploadFile(file) {
    const statusDiv = document.getElementById('upload-status');
    const statusText = document.getElementById('upload-status-text');
    
    statusDiv.classList.remove('hidden');
    statusText.textContent = `Uploading: ${file.name}...`;
    
    try {
        const result = await DocumentsAPI.upload(file);
        
        if (result.success) {
            statusText.textContent = `✅ Upload successful! Auto-vectorizing...`;
            
            // Auto-index the uploaded document
            try {
                const indexResult = await DocumentsAPI.index(result.document.doc_id);
                statusText.textContent = `✅ Complete! Created ${indexResult.chunk_count} vectors`;
            } catch (indexError) {
                statusText.textContent = `⚠️ Upload successful, but vectorization failed: ${indexError.message}`;
            }
            
            // Refresh document list and stats
            loadDocuments();
            loadStats();
        }
    } catch (error) {
        statusText.textContent = `❌ Upload failed: ${error.message}`;
    }
    
    // Hide status after 5 seconds
    setTimeout(() => {
        statusDiv.classList.add('hidden');
    }, 5000);
}

async function indexDocument(docId) {
    if (!confirm('Are you sure you want to vectorize this document?')) return;
    
    try {
        const result = await DocumentsAPI.index(docId);
        alert(`Vectorization complete! Created ${result.chunk_count} vector chunks`);
        loadDocuments();
        loadStats();
    } catch (error) {
        alert(`Vectorization failed: ${error.message}`);
    }
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document? Related vector data will also be deleted.')) return;
    
    try {
        await DocumentsAPI.delete(docId);
        loadDocuments();
        loadStats();
    } catch (error) {
        alert(`Delete failed: ${error.message}`);
    }
}

// ============ Tickets ============

async function loadTickets() {
    const listDiv = document.getElementById('ticket-list');
    
    try {
        const result = await AgentAPI.getTickets();
        const tickets = result.tickets;
        
        document.getElementById('stat-tickets').textContent = tickets.length;
        
        const statusColors = {
            'Resolved': 'bg-green-100 text-green-700',
            'In Progress': 'bg-blue-100 text-blue-700',
            'Pending': 'bg-yellow-100 text-yellow-700',
            'Closed': 'bg-gray-100 text-gray-700',
        };
        
        listDiv.innerHTML = tickets.map(ticket => `
            <div class="border rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div class="flex items-start justify-between mb-2">
                    <div class="font-medium text-gray-800">${ticket.ticket_id}</div>
                    <span class="text-xs px-2 py-0.5 rounded-full ${statusColors[ticket.status] || 'bg-gray-100'}">
                        ${ticket.status}
                    </span>
                </div>
                <div class="text-sm font-medium text-gray-700 mb-1">${escapeHtml(ticket.title)}</div>
                <div class="text-xs text-gray-500 mb-2">${escapeHtml(ticket.description)}</div>
                <div class="flex justify-between text-xs text-gray-400">
                    <span>Submitter: ${escapeHtml(ticket.submitter)}</span>
                    <span>Assignee: ${escapeHtml(ticket.assignee || 'Unassigned')}</span>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        listDiv.innerHTML = `
            <div class="text-center text-gray-400 py-4 col-span-2">
                Load failed: ${error.message}
            </div>
        `;
    }
}

// ============ Danger Zone ============

async function clearKnowledgeBase() {
    if (!confirm('⚠️ Are you sure you want to clear the entire knowledge base? This action cannot be undone!')) return;
    if (!confirm('Confirm again: All vector data will be permanently deleted. Are you sure you want to continue?')) return;
    
    try {
        await AdminAPI.clearKB();
        alert('Knowledge base cleared');
        loadStats();
    } catch (error) {
        alert(`Operation failed: ${error.message}`);
    }
}

// ============ File Upload UI ============

function setupFileInput() {
    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });
}

function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // Click to open file picker
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag over
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    // Drop
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

// ============ Utilities ============

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}