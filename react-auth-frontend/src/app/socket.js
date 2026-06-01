// src/app/socket.js
class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect(token, userId, deviceId, onLogout) {
    // IMPORTANT: Remove extra slash and add token as query parameter
    const wsUrl = `${process.env.REACT_APP_WS_URL}/?token=${token}`;
    console.log('🔌 Connecting WebSocket to:', wsUrl);
    
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      this.notifyListeners('connected', { message: 'Connected successfully' });
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', data);
        
        if (data.type === 'LOGOUT') {
          console.log('🚪 Logout notification received:', data.message);
          if (onLogout) {
            onLogout(data);
          }
          this.notifyListeners('logout', data);
        } else {
          this.notifyListeners('message', data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.notifyListeners('error', error);
    };

    this.socket.onclose = (event) => {
      console.log('🔌 WebSocket disconnected:', event.code, event.reason);
      this.notifyListeners('disconnected', { code: event.code, reason: event.reason });
    };
  }

  disconnect() {
    if (this.socket) {
      console.log('🔌 Disconnecting WebSocket...');
      this.socket.close();
      this.socket = null;
    }
  }

  addEventListener(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  removeEventListener(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyListeners(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}

export const webSocketService = new WebSocketService();