/**
 * WebSocket Connection Manager
 * Handles real-time communication with the backend server
 */

class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 seconds initial delay
        this.messageHandlers = {};
        this.url = "ws://localhost:8000/ws";
    }

    /**
     * Connect to the WebSocket server
     * @returns {Promise} Resolves when connected, rejects on failure
     */
    connect() {
        return new Promise((resolve, reject) => {
            if (this.socket && this.isConnected) {
                resolve();
                return;
            }

            this.socket = new WebSocket(this.url);

            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this._updateConnectionStatus('connected', 'Connected');
                resolve();
            };

            this.socket.onclose = (event) => {
                console.log('WebSocket disconnected', event);
                this.isConnected = false;
                this._updateConnectionStatus('disconnected', 'Disconnected');
                this._attemptReconnect();
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (!this.isConnected) {
                    reject(error);
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._handleMessage(data);
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };
        });
    }

    /**
     * Register a message handler
     * @param {string} type - Message type to handle
     * @param {function} handler - Handler function
     */
    on(type, handler) {
        if (!this.messageHandlers[type]) {
            this.messageHandlers[type] = [];
        }
        this.messageHandlers[type].push(handler);
    }

    /**
     * Send a message to the server
     * @param {Object} data - Message data to send
     * @returns {boolean} - Success status
     */
    send(data) {
        if (!this.socket || !this.isConnected) {
            console.error('Cannot send message: WebSocket not connected');
            return false;
        }

        try {
            this.socket.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error sending message:', error);
            return false;
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.isConnected = false;
            this._updateConnectionStatus('disconnected', 'Disconnected');
        }
    }

    /**
     * Handle incoming message and route to appropriate handlers
     * @param {Object} data - Message data
     * @private
     */
    _handleMessage(data) {
        const type = data.type;
        
        if (type && this.messageHandlers[type]) {
            this.messageHandlers[type].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in message handler for '${type}':`, error);
                }
            });
        }
    }

    /**
     * Attempt to reconnect to the WebSocket server
     * @private
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
        
        this._updateConnectionStatus('connecting', 'Reconnecting...');
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }
        }, delay);
    }

    /**
     * Update connection status in UI
     * @param {string} status - Status class
     * @param {string} text - Status text
     * @private
     */
    _updateConnectionStatus(status, text) {
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    }
}

// Create global instance
const websocketManager = new WebSocketManager();
