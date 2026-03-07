/**
 * INASC Chat Widget — widget.js
 * Conecta al backend FastAPI vía WebSocket (/ws/chat/{client_id}).
 * Patrón: the widget assumes the HTML skeleton already exists (built by widget.html).
 */

(function () {
    'use strict';

    /* ── Configuración ─────────────────────────────────────── */
    const CONFIG = {
        // Detecta automáticamente el host del servidor que sirvió el HTML.
        // En desarrollo: ws://127.0.0.1:8000/ws/chat/{id}
        // En producción: wss://inasc.com.co/ws/chat/{id}
        wsProtocol: location.protocol === 'https:' ? 'wss' : 'ws',
        wsHost: location.host,          // e.g. "127.0.0.1:8000" o "inasc.com.co"
        reconnectBaseMs: 1500,          // espera inicial antes de reconectar
        reconnectMaxMs: 30000,          // tope de backoff exponencial
        reconnectMaxTries: 8,           // intentos máximos antes de desistir
        greetingDelay: 600,             // ms para mostrar saludo de bienvenida
        userName: 'Visitante',          // nombre por defecto si no se captura
    };

    /* ── Estado de la sesión ───────────────────────────────── */
    const STATE = {
        clientId: generateClientId(),
        ws: null,
        isOpen: false,           // panel visible
        isSending: false,        // esperando respuesta del LLM
        reconnectTries: 0,
        reconnectTimer: null,
        unreadCount: 0,
    };

    /* ── Referencias DOM ───────────────────────────────────── */
    const launcher = document.getElementById('inasc-chat-launcher');
    const panel = document.getElementById('inasc-chat-panel');
    const messages = document.getElementById('inasc-chat-messages');
    const input = document.getElementById('inasc-chat-input');
    const sendBtn = document.getElementById('inasc-send-btn');
    const typingRow = document.getElementById('inasc-typing');
    const connStatus = document.getElementById('inasc-conn-status');
    const badge = document.getElementById('inasc-notif-badge');

    /* ================================================================
       CICLO DE VIDA DEL WEBSOCKET
       ================================================================ */

    function buildWsUrl() {
        return `${CONFIG.wsProtocol}://${CONFIG.wsHost}/ws/chat/${STATE.clientId}`;
    }

    function connectWs() {
        setConnStatus('connecting', 'Conectando con el asistente...');

        const ws = new WebSocket(buildWsUrl());
        STATE.ws = ws;

        ws.onopen = function () {
            STATE.reconnectTries = 0;
            clearTimeout(STATE.reconnectTimer);
            setConnStatus(null);           // ocultar banner
            setInputEnabled(true);
            console.debug('[INASC Widget] WebSocket conectado:', buildWsUrl());

            // Saludo automático al conectar por primera vez
            if (messages.children.length === 0) {
                setTimeout(showWelcomeMessage, CONFIG.greetingDelay);
            }
        };

        ws.onmessage = function (event) {
            let data;
            try { data = JSON.parse(event.data); }
            catch { data = { role: 'agent', content: event.data }; }

            hideTyping();
            appendMessage('agent', data.content || '');
            STATE.isSending = false;
            setInputEnabled(true);

            // Badge si el panel está cerrado
            if (!STATE.isOpen) {
                STATE.unreadCount++;
                showBadge(STATE.unreadCount);
            }
        };

        ws.onerror = function () {
            console.warn('[INASC Widget] Error en WebSocket.');
        };

        ws.onclose = function (event) {
            hideTyping();
            STATE.isSending = false;
            setInputEnabled(false);

            if (event.wasClean) {
                console.debug('[INASC Widget] Conexión cerrada limpiamente.');
                return;
            }

            // Reconexión con backoff exponencial
            if (STATE.reconnectTries < CONFIG.reconnectMaxTries) {
                const delay = Math.min(
                    CONFIG.reconnectBaseMs * Math.pow(1.8, STATE.reconnectTries),
                    CONFIG.reconnectMaxMs
                );
                STATE.reconnectTries++;
                setConnStatus('reconnecting',
                    `Reconectando... (intento ${STATE.reconnectTries})`);
                STATE.reconnectTimer = setTimeout(connectWs, delay);
            } else {
                setConnStatus('error',
                    'Sin conexión con el asistente. Intenta recargar la página.');
            }
        };
    }

    function disconnectWs() {
        clearTimeout(STATE.reconnectTimer);
        if (STATE.ws && STATE.ws.readyState <= WebSocket.OPEN) {
            STATE.ws.close(1000, 'Widget cerrado por el usuario');
        }
        STATE.ws = null;
    }

    /* ================================================================
       ENVÍO Y RECEPCIÓN DE MENSAJES
       ================================================================ */

    function sendMessage() {
        if (STATE.isSending) return;

        const text = input.value.trim();
        if (!text) return;
        if (!STATE.ws || STATE.ws.readyState !== WebSocket.OPEN) {
            setConnStatus('error', 'Sin conexión. Espera un momento...');
            return;
        }

        // Mostrar la burbuja del usuario inmediatamente
        appendMessage('user', text);
        input.value = '';
        autoResizeInput();

        // Mostrar typing y deshabilitar input mientras esperamos
        showTyping();
        STATE.isSending = true;
        setInputEnabled(false);

        // Enviar al backend
        const payload = {
            text: text,
            user_name: CONFIG.userName,
        };
        STATE.ws.send(JSON.stringify(payload));
    }

    /* ================================================================
       MANIPULACIÓN DEL DOM
       ================================================================ */

    function appendMessage(role, content) {
        // Clonar plantilla o construir manualmente
        const row = document.createElement('div');
        row.className = `inasc-bubble-row ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'inasc-bubble';
        bubble.textContent = content;

        if (role === 'agent') {
            const miniAvatar = document.createElement('div');
            miniAvatar.className = 'inasc-mini-avatar';
            miniAvatar.innerHTML = SVG_ROBOT;
            row.appendChild(miniAvatar);
        }

        row.appendChild(bubble);
        messages.appendChild(row);
        scrollToBottom();
    }

    function showTyping() {
        typingRow.classList.add('visible');
        scrollToBottom();
    }

    function hideTyping() {
        typingRow.classList.remove('visible');
    }

    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function setInputEnabled(enabled) {
        input.disabled = !enabled;
        sendBtn.disabled = !enabled;
        if (enabled) input.focus();
    }

    function setConnStatus(type, text) {
        if (!type) {
            connStatus.className = '';
            connStatus.style.display = 'none';
            return;
        }
        connStatus.className = type;
        connStatus.textContent = text;
        connStatus.style.display = 'block';
    }

    function showBadge(count) {
        badge.textContent = count > 9 ? '9+' : count;
        badge.style.display = 'flex';
    }

    function hideBadge() {
        STATE.unreadCount = 0;
        badge.style.display = 'none';
    }

    function showWelcomeMessage() {
        appendMessage('agent',
            '¡Hola! 👋 Soy el Asistente Virtual de INASC. Estoy aquí para ayudarte con ' +
            'información sobre equipos de laboratorio, metrología y servicios técnicos. ' +
            '¿En qué puedo ayudarte hoy?'
        );
    }

    /* ================================================================
       APERTURA / CIERRE DEL PANEL
       ================================================================ */

    function openPanel() {
        STATE.isOpen = true;
        panel.classList.add('is-visible');
        launcher.classList.add('is-open');
        hideBadge();

        // Conectar WS la primera vez (o reconectar si estaba cerrado)
        if (!STATE.ws || STATE.ws.readyState > WebSocket.OPEN) {
            connectWs();
        } else {
            setInputEnabled(true);
        }
    }

    function closePanel() {
        STATE.isOpen = false;
        panel.classList.remove('is-visible');
        launcher.classList.remove('is-open');
        // NO desconectamos aquí para que el historial persista en la sesión.
        // La desconexión ocurre al salir de la página (beforeunload).
    }

    function togglePanel() {
        STATE.isOpen ? closePanel() : openPanel();
    }

    /* ================================================================
       REDIMENSIONADO AUTOMÁTICO DEL TEXTAREA
       ================================================================ */

    function autoResizeInput() {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    }

    /* ================================================================
       GENERACIÓN DE CLIENT ID DE SESIÓN
       ================================================================ */

    function generateClientId() {
        // Reutilizar el id de sesión si el usuario refresca la página
        const key = 'inasc_chat_client_id';
        let id = sessionStorage.getItem(key);
        if (!id) {
            // crypto.randomUUID() disponible en todos los navegadores modernos + HTTPS
            id = (typeof crypto !== 'undefined' && crypto.randomUUID)
                ? crypto.randomUUID()
                : 'web_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9);
            sessionStorage.setItem(key, id);
        }
        return id;
    }

    /* ================================================================
       EVENT LISTENERS
       ================================================================ */

    launcher.addEventListener('click', togglePanel);

    sendBtn.addEventListener('click', sendMessage);

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    input.addEventListener('input', autoResizeInput);

    // Desconectar limpiamente al salir de la página
    window.addEventListener('beforeunload', disconnectWs);

    /* ================================================================
       SVG INLINE — evita dependencia de íconos externos
       ================================================================ */

    // Ícono de chat (para el launcher cuando está cerrado)
    const SVG_CHAT = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="icon-chat">
    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
  </svg>`;

    // Ícono X (para el launcher cuando está abierto)
    const SVG_CLOSE = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="icon-close">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
  </svg>`;

    // Ícono robot para mini-avatar del agente
    const SVG_ROBOT = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h3a3 3 0 0 1 3 3v1h1a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-1v1a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-1H3a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h1v-1a3 3 0 0 1 3-3h3V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2zm-2 9a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3zm4 0a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3zm-4 4h4l-1 2h-2l-1-2z"/>
  </svg>`;

    // Ícono de envío (paper plane)
    const SVG_SEND = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
  </svg>`;

    // Inyectar SVGs en el DOM
    launcher.innerHTML = SVG_CHAT + SVG_CLOSE + `
    <div id="inasc-notif-badge" style="display:none">0</div>`;

    sendBtn.innerHTML = SVG_SEND;

    // Reasignar badge tras re-render del launcher
    // (el badge original fue reemplazado por innerHTML, necesitamos la nueva referencia local)
    const liveBadge = document.getElementById('inasc-notif-badge');

    function showBadgeLive(count) {
        liveBadge.textContent = count > 9 ? '9+' : count;
        liveBadge.style.display = 'flex';
    }
    function hideBadgeLive() {
        STATE.unreadCount = 0;
        liveBadge.style.display = 'none';
    }

    // Reemplazar las funciones del closure con las que usan la referencia real del DOM
    // (las funciones showBadge/hideBadge arriba son obsoletas por el innerHTML override)
    Object.defineProperty(window, 'inascHideBadge', { value: hideBadgeLive });

})();
