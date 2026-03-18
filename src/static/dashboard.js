/**
 * INASC — Dashboard de Asesor JS
 */

let currentConversationId = null;
let tenantId = new URLSearchParams(window.location.search).get('tenant_id') || 'inasc_001';

document.getElementById('tenant-badge').innerText = `Tenant: ${tenantId}`;

// --- API Calls ---

async function fetchConversations() {
    try {
        const response = await fetch('/api/dashboard/conversations', {
            headers: { 'X-Tenant-ID': tenantId }
        });
        const conversations = await response.json();
        renderChatList(conversations);
    } catch (err) {
        console.error("Error fetching conversations:", err);
    }
}

async function loadMessages(conversationId) {
    try {
        const response = await fetch(`/api/dashboard/conversations/${conversationId}/messages`, {
            headers: { 'X-Tenant-ID': tenantId }
        });
        const messages = await response.json();
        renderMessages(messages);
    } catch (err) {
        console.error("Error loading messages:", err);
    }
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content || !currentConversationId) return;

    input.value = '';
    input.placeholder = 'Enviando...';
    input.disabled = true;

    try {
        const response = await fetch(`/api/dashboard/conversations/${currentConversationId}/reply`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            },
            body: JSON.stringify({ content })
        });
        
        if (response.ok) {
            await loadMessages(currentConversationId);
        } else {
            alert("Error enviando mensaje.");
        }
    } catch (err) {
        console.error("Error sending response:", err);
    } finally {
        input.placeholder = 'Escribe tu respuesta...';
        input.disabled = false;
        input.focus();
    }
}

async function closeConversation() {
    if (!currentConversationId || !confirm("¿Quieres devolver el control al BOT?")) return;

    try {
        const response = await fetch(`/api/dashboard/conversations/${currentConversationId}/close`, {
            method: 'POST',
            headers: { 'X-Tenant-ID': tenantId }
        });
        
        if (response.ok) {
            currentConversationId = null;
            document.getElementById('header-actions').style.display = 'none';
            document.getElementById('chat-input-area').style.display = 'none';
            document.getElementById('chat-messages').innerHTML = '<div class="empty-state">Conversación cerrada.</div>';
            fetchConversations();
        }
    } catch (err) {
        console.error("Error closing conversation:", err);
    }
}

// --- Rendering ---

function renderChatList(conversations) {
    const list = document.getElementById('chat-list');
    list.innerHTML = conversations.length ? '' : '<div style="padding: 20px; color: #94a3b8; font-size: 0.8rem;">No hay chats pendientes.</div>';

    conversations.forEach(conv => {
        const div = document.createElement('div');
        div.className = `chat-item ${currentConversationId == conv.id ? 'active' : ''}`;
        div.innerHTML = `
            <span class="chat-name">${conv.full_name || 'Anónimo'}</span>
            <div class="chat-meta">${conv.platform.toUpperCase()} · ${conv.platform_user_id}</div>
        `;
        div.onclick = () => selectChat(conv);
        list.appendChild(div);
    });
}

function selectChat(conv) {
    currentConversationId = conv.id;
    document.getElementById('current-user-name').innerText = conv.full_name || 'Anónimo';
    document.getElementById('current-platform').innerText = conv.platform.toUpperCase();
    document.getElementById('header-actions').style.display = 'block';
    document.getElementById('chat-input-area').style.display = 'flex';
    
    // Refresh selection highlight
    fetchConversations();
    loadMessages(conv.id);
}

function renderMessages(messages) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    
    messages.forEach(msg => {
        const div = document.createElement('div');
        // Simple heuristic: user messages vs assistant/bot
        div.className = `message ${msg.role == 'user' ? 'user' : (msg.role == 'assistant' ? 'assistant' : 'bot')}`;
        div.innerText = msg.content;
        container.appendChild(div);
    });
    
    container.scrollTop = container.scrollHeight;
}

// --- Init ---

fetchConversations();
setInterval(fetchConversations, 5000); // Polling cada 5 segs

// Send with Enter
document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
