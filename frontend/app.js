// Frontend Application Logic

const API_BASE = 'http://localhost:8000';

let currentSessionId = null;
let currentMode = 'C3'; // 'C1' for regular, 'C3' for adaptive
let donationContext = {
    organization: "Children's Education Fund",
    cause: "providing education to underprivileged children",
    amounts: "200, 500, 1000",
    impact: "₹200 provides school supplies for 5 children for a month"
};

// DOM Elements
const modeToggle = document.getElementById('modeToggle');
const setupBtn = document.getElementById('setupBtn');
const resetBtn = document.getElementById('resetBtn');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const metricsContent = document.getElementById('metricsContent');
const setupModal = document.getElementById('setupModal');
const closeModal = document.getElementById('closeModal');
const saveScenario = document.getElementById('saveScenario');
const cancelSetup = document.getElementById('cancelSetup');
const connectionStatus = document.getElementById('connectionStatus');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set initial mode (Adaptive = checked)
    modeToggle.checked = true;
    
    // Event Listeners
    modeToggle.addEventListener('change', handleModeChange);
    setupBtn.addEventListener('click', () => setupModal.classList.add('show'));
    closeModal.addEventListener('click', () => setupModal.classList.remove('show'));
    cancelSetup.addEventListener('click', () => setupModal.classList.remove('show'));
    saveScenario.addEventListener('click', handleScenarioSave);
    sendBtn.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    resetBtn.addEventListener('click', handleReset);
    
    // Close modal on outside click
    setupModal.addEventListener('click', (e) => {
        if (e.target === setupModal) {
            setupModal.classList.remove('show');
        }
    });
    
    // Check backend connection first
    updateConnectionStatus('checking');
    checkBackendConnection().then(connected => {
        if (connected) {
            updateConnectionStatus('connected');
            // Initialize scenario setup
            initializeScenario();
        } else {
            updateConnectionStatus('disconnected');
            showConnectionError();
        }
    });
    
    // Update mode label on page load
    updateModeLabel();
});

function updateModeLabel() {
    // This function can be used to update UI based on current mode
    const modeText = currentMode === 'C3' ? 'Adaptive' : 'Regular';
    console.log(`Current mode: ${modeText}`);
}

async function checkBackendConnection() {
    try {
        // Create a timeout promise
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Connection timeout')), 5000);
        });
        
        // Try health endpoint first, fallback to root
        const endpoints = ['/health', '/'];
        for (const endpoint of endpoints) {
            try {
                const fetchPromise = fetch(`${API_BASE}${endpoint}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const response = await Promise.race([fetchPromise, timeoutPromise]);
                if (response && response.ok) {
                    return true;
                }
            } catch (e) {
                // Try next endpoint
                continue;
            }
        }
        return false;
    } catch (error) {
        console.error('Backend connection check failed:', error);
        return false;
    }
}

function updateConnectionStatus(status) {
    if (!connectionStatus) return;
    
    connectionStatus.style.display = 'flex';
    connectionStatus.className = 'connection-status';
    
    const statusText = connectionStatus.querySelector('.status-text');
    
    switch(status) {
        case 'checking':
            connectionStatus.classList.add('checking');
            statusText.textContent = 'Checking...';
            break;
        case 'connected':
            connectionStatus.classList.add('connected');
            statusText.textContent = 'Connected';
            break;
        case 'disconnected':
            connectionStatus.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
            break;
    }
}

function showConnectionError() {
    chatMessages.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
            <h3 style="color: var(--danger-color); margin-bottom: 1rem;">Backend Not Connected</h3>
            <p style="margin-bottom: 1rem;">The backend server is not running or not accessible.</p>
            <div style="background: var(--bg-light); padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: left;">
                <p style="margin-bottom: 0.5rem;"><strong>To fix this:</strong></p>
                <ol style="margin-left: 1.5rem; line-height: 1.8;">
                    <li>Open a terminal/command prompt</li>
                    <li>Navigate to the project directory</li>
                    <li>Run: <code style="background: var(--bg-darker); padding: 0.2rem 0.4rem; border-radius: 4px;">python start_backend.py</code></li>
                    <li>Wait for "Backend will be available at: http://localhost:8000"</li>
                    <li>Click the "Retry Connection" button below or refresh this page</li>
                </ol>
            </div>
            <button onclick="retryConnection()" class="btn btn-primary" style="margin-top: 1rem;">Retry Connection</button>
        </div>
    `;
    messageInput.disabled = true;
    sendBtn.disabled = true;
}

async function retryConnection() {
    updateConnectionStatus('checking');
    const connected = await checkBackendConnection();
    if (connected) {
        updateConnectionStatus('connected');
        // Clear error message and initialize
        chatMessages.innerHTML = '';
        await initializeScenario();
    } else {
        updateConnectionStatus('disconnected');
        showConnectionError();
    }
}

async function initializeScenario() {
    try {
        // Setup scenario first
        const response = await fetch(`${API_BASE}/api/scenario/setup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                organization: donationContext.organization,
                cause: donationContext.cause,
                amounts: donationContext.amounts,
                impact: donationContext.impact
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to setup scenario: ${errorText}`);
        }
        
        // Create session
        await createSession();
    } catch (error) {
        console.error('Initialization error:', error);
        if (error.message.includes('fetch') || error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            updateConnectionStatus('disconnected');
            showConnectionError();
        } else {
            updateConnectionStatus('disconnected');
            showError('Failed to initialize: ' + error.message);
        }
    }
}

async function createSession() {
    try {
        const response = await fetch(`${API_BASE}/api/session/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                condition: currentMode,
                donation_context: donationContext
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to create session: ${errorText}`);
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Show opening message
        addMessage('agent', data.opening_message);
        
        // Enable input
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
        
        // Update metrics
        updateMetrics();
        
        // Start periodic connection check
        startConnectionMonitoring();
    } catch (error) {
        console.error('Session creation error:', error);
        if (error.message.includes('fetch') || error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            updateConnectionStatus('disconnected');
            showConnectionError();
        } else {
            updateConnectionStatus('disconnected');
            showError('Failed to create session: ' + error.message);
        }
    }
}

let connectionMonitorInterval = null;

function startConnectionMonitoring() {
    // Clear any existing interval
    if (connectionMonitorInterval) {
        clearInterval(connectionMonitorInterval);
    }
    
    // Check connection every 30 seconds
    connectionMonitorInterval = setInterval(async () => {
        const connected = await checkBackendConnection();
        if (connected) {
            updateConnectionStatus('connected');
        } else {
            updateConnectionStatus('disconnected');
        }
    }, 30000);
}

async function handleModeChange() {
    const newMode = modeToggle.checked ? 'C3' : 'C1';
    
    if (newMode === currentMode) return;
    
    currentMode = newMode;
    
    // Reset conversation when switching modes
    if (currentSessionId) {
        // Clear chat and create new session with new mode
        chatMessages.innerHTML = '';
        metricsContent.innerHTML = '<div class="metrics-placeholder"><p>Start a conversation to see metrics</p></div>';
        await createSession();
    }
}

async function handleSendMessage() {
    const message = messageInput.value.trim();
    if (!message || !currentSessionId) return;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/session/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        const data = await response.json();
        
        // Add agent response
        addMessage('agent', data.agent_msg);
        
        // Update metrics
        updateMetricsDisplay(data.metrics);
        
        // Check if conversation ended
        if (data.stop) {
            messageInput.disabled = true;
            sendBtn.disabled = true;
            showNotification('Conversation ended: ' + (data.reason || 'Session completed'));
        } else {
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    } catch (error) {
        console.error('Send message error:', error);
        if (error.message.includes('fetch') || error.message.includes('Failed to fetch') || error.name === 'TypeError') {
            updateConnectionStatus('disconnected');
            showConnectionError();
        } else {
            showError('Failed to send message: ' + error.message);
            messageInput.disabled = false;
            sendBtn.disabled = false;
        }
    }
}

async function handleReset() {
    if (!currentSessionId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/session/${currentSessionId}/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) throw new Error('Failed to reset session');
        
        // Clear chat
        chatMessages.innerHTML = '';
        
        // Show opening message
        const data = await response.json();
        addMessage('agent', data.opening_message);
        
        // Reset metrics
        metricsContent.innerHTML = '<div class="metrics-placeholder"><p>Start a conversation to see metrics</p></div>';
        
        // Enable input
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    } catch (error) {
        console.error('Reset error:', error);
        showError('Failed to reset session. Creating new session...');
        await createSession();
    }
}

async function handleScenarioSave() {
    donationContext = {
        organization: document.getElementById('orgName').value || "Children's Education Fund",
        cause: document.getElementById('cause').value || "providing education to underprivileged children",
        amounts: document.getElementById('amounts').value || "200, 500, 1000",
        impact: document.getElementById('impact').value || "₹200 provides school supplies for 5 children for a month"
    };
    
    setupModal.classList.remove('show');
    
    // Reset and create new session with new context
    if (currentSessionId) {
        await handleReset();
    } else {
        await createSession();
    }
}

function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = sender === 'user' ? 'You' : 'Agent';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(label);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function updateMetrics() {
    if (!currentSessionId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/session/${currentSessionId}/metrics`);
        if (!response.ok) return;
        
        const data = await response.json();
        updateMetricsDisplay(data);
    } catch (error) {
        console.error('Metrics update error:', error);
    }
}

function updateMetricsDisplay(metrics) {
    if (!metrics) return;
    
    const beliefColor = metrics.belief > 0.6 ? 'positive' : (metrics.belief > 0.3 ? 'warning' : 'danger');
    const trustColor = metrics.trust > 0.7 ? 'positive' : (metrics.trust > 0.5 ? 'warning' : 'danger');
    
    metricsContent.innerHTML = `
        <div class="metric-card">
            <h3>Donation Probability</h3>
            <div class="metric-value ${beliefColor}">${(metrics.belief * 100).toFixed(1)}%</div>
            <div class="metric-delta ${metrics.delta_belief >= 0 ? 'positive' : 'negative'}">
                ${metrics.delta_belief >= 0 ? '+' : ''}${(metrics.delta_belief * 100).toFixed(1)}%
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill ${beliefColor}" style="width: ${metrics.belief * 100}%"></div>
                </div>
            </div>
        </div>
        
        <div class="metric-card">
            <h3>Trust Score</h3>
            <div class="metric-value ${trustColor}">${(metrics.trust * 100).toFixed(1)}%</div>
            <div class="metric-delta ${metrics.delta_trust >= 0 ? 'positive' : 'negative'}">
                ${metrics.delta_trust >= 0 ? '+' : ''}${(metrics.delta_trust * 100).toFixed(1)}%
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill ${trustColor}" style="width: ${metrics.trust * 100}%"></div>
                </div>
            </div>
            ${metrics.recovery_mode ? '<div class="status-badge recovery">RECOVERY MODE</div>' : '<div class="status-badge active">ACTIVE</div>'}
        </div>
        
        <div class="metric-card">
            <h3>Turn Information</h3>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: var(--text-secondary);">Turn:</span>
                <span style="font-weight: 600;">${metrics.turn || 0}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: var(--text-secondary);">Rejection Type:</span>
                <span style="font-weight: 600; text-transform: uppercase;">${metrics.rejection_type || 'none'}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: var(--text-secondary);">Sentiment:</span>
                <span style="font-weight: 600; text-transform: capitalize;">${metrics.sentiment || 'neutral'}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">Consecutive Rejections:</span>
                <span style="font-weight: 600;">${metrics.consec_reject || 0}</span>
            </div>
        </div>
        
        <div class="metric-card">
            <h3>Strategy Weights</h3>
            <div class="strategy-weights">
                ${Object.entries(metrics.strategy_weights || {})
                    .sort((a, b) => b[1] - a[1])
                    .map(([strategy, weight]) => `
                        <div class="strategy-item">
                            <div class="strategy-name">${strategy}</div>
                            <div class="strategy-bar-container">
                                <div class="strategy-bar" style="width: ${weight * 100}%"></div>
                            </div>
                            <div class="strategy-value">${(weight * 100).toFixed(1)}%</div>
                        </div>
                    `).join('')}
            </div>
        </div>
    `;
}

function showError(message) {
    // Simple error notification - can be enhanced
    alert('Error: ' + message);
}

function showNotification(message) {
    // Simple notification - can be enhanced
    console.log('Notification:', message);
}
