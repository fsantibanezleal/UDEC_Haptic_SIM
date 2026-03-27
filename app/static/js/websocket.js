/**
 * WebSocket manager for real-time simulation communication.
 *
 * Maintains a persistent connection to the FastAPI backend,
 * sends probe updates and settings changes, and dispatches
 * received scene state to registered callbacks.
 */
class SimWebSocket {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.onStateUpdate = null; // callback(state)
        this.reconnectDelay = 1000;
        this._reconnectTimer = null;
    }

    /**
     * Connect to the WebSocket endpoint.
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws`;

        try {
            this.ws = new WebSocket(url);
        } catch (e) {
            console.error('WebSocket creation failed:', e);
            this._scheduleReconnect();
            return;
        }

        this.ws.onopen = () => {
            this.connected = true;
            this._updateStatus(true);
            console.log('WebSocket connected');
            // Send initial step to get scene state
            this.send({ type: 'step' });
        };

        this.ws.onmessage = (event) => {
            try {
                const state = JSON.parse(event.data);
                if (this.onStateUpdate) {
                    this.onStateUpdate(state);
                }
            } catch (e) {
                console.error('Failed to parse WS message:', e);
            }
        };

        this.ws.onclose = () => {
            this.connected = false;
            this._updateStatus(false);
            console.log('WebSocket closed');
            this._scheduleReconnect();
        };

        this.ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }

    /**
     * Send a JSON message to the server.
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    /**
     * Send probe position update.
     */
    sendProbe(x, y, z) {
        this.send({ type: 'probe', x, y, z });
    }

    /**
     * Send settings update.
     */
    sendSettings(settings) {
        this.send({ type: 'settings', ...settings });
    }

    /**
     * Send transform command.
     */
    sendTransform(bodyIndex, transformType, params) {
        this.send({
            type: 'transform',
            body_index: bodyIndex,
            transform_type: transformType,
            ...params,
        });
    }

    /**
     * Send scene reset command.
     */
    sendReset() {
        this.send({ type: 'reset' });
    }

    /**
     * Request a simulation step (used for periodic updates).
     */
    requestStep() {
        this.send({ type: 'step' });
    }

    disconnect() {
        if (this._reconnectTimer) {
            clearTimeout(this._reconnectTimer);
        }
        if (this.ws) {
            this.ws.close();
        }
    }

    _scheduleReconnect() {
        if (this._reconnectTimer) clearTimeout(this._reconnectTimer);
        this._reconnectTimer = setTimeout(() => {
            console.log('Attempting reconnect...');
            this.connect();
        }, this.reconnectDelay);
    }

    _updateStatus(connected) {
        const el = document.getElementById('wsStatus');
        if (el) {
            el.textContent = connected ? 'Connected' : 'Disconnected';
            el.className = 'status ' + (connected ? 'connected' : 'disconnected');
        }
    }
}

// Global instance
window.simWS = new SimWebSocket();
