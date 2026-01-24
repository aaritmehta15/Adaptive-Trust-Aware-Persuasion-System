// Frontend Application Logic

// Use environment variable or default to localhost
// For deployment: Set this to your Render URL
const API_BASE = window.DEPLOYED_API_URL || 'http://localhost:8000';

// DEPLOYMENT: Uncomment and update this line with your Render URL
// const API_BASE = 'https://your-app-name.onrender.com';

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

    switch (status) {
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
            // Add graph button when conversation ends
            addGraphButton();
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

    // Hide metrics panel for C1 (Regular) mode
    const metricsPanel = document.querySelector('.metrics-panel');
    if (currentMode === 'C1') {
        if (metricsPanel) {
            metricsPanel.style.display = 'none';
        }
        return;
    } else {
        if (metricsPanel) {
            metricsPanel.style.display = 'flex';
        }
    }

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

function addGraphButton() {
    // Check if button already exists
    if (document.getElementById('showGraphBtn')) return;

    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = 'text-align: center; padding: 1rem; margin-top: 1rem;';
    
    const graphButton = document.createElement('button');
    graphButton.id = 'showGraphBtn';
    graphButton.className = 'btn btn-primary';
    graphButton.textContent = 'View Conversation Graph';
    graphButton.onclick = showConversationGraph;
    
    buttonContainer.appendChild(graphButton);
    chatMessages.appendChild(buttonContainer);
}

async function showConversationGraph() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/session/${currentSessionId}/metrics`);
        if (!response.ok) {
            showError('Failed to fetch graph data');
            return;
        }

        const data = await response.json();
        
        // Create modal for graph
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.id = 'graphModal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h2>Conversation Analytics</h2>
                    <button class="modal-close" onclick="document.getElementById('graphModal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <canvas id="conversationChart" style="max-height: 400px;"></canvas>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Load Chart.js if not already loaded
        if (typeof Chart === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.onload = () => renderChart(data);
            document.head.appendChild(script);
        } else {
            renderChart(data);
        }

        // Close modal on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    } catch (error) {
        console.error('Graph error:', error);
        showError('Failed to load graph: ' + error.message);
    }
}

function renderChart(data) {
    const ctx = document.getElementById('conversationChart');
    if (!ctx) return;

    const beliefHistory = data.belief_history || [];
    const trustHistory = data.trust_history || [];
    const turns = beliefHistory.length;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: turns }, (_, i) => `Turn ${i}`),
            datasets: [
                {
                    label: 'Donation Probability',
                    data: beliefHistory.map(v => (v * 100).toFixed(1)),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Trust Score',
                    data: trustHistory.map(v => (v * 100).toFixed(1)),
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#f1f5f9'
                    }
                },
                title: {
                    display: true,
                    text: 'Trust Score and Donation Probability Over Time',
                    color: '#f1f5f9'
                }
            },
            scales: {
                x: {
                    ticks: { color: '#cbd5e1' },
                    grid: { color: '#475569' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    min: 0,
                    max: 100,
                    ticks: { 
                        color: '#cbd5e1',
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { color: '#475569' }
                }
            }
        }
    });
}
