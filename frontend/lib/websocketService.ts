/* eslint-disable @typescript-eslint/no-explicit-any */

type WebSocketEventListener = (data: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private docId: string | null = null;
  private listeners: Map<string, WebSocketEventListener[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  connect(docId: string): void {
    this.docId = docId;
    
    if (this.socket) {
      this.socket.close();
    }

    try {
      this.socket = new WebSocket(`ws://localhost:8000/ws/${docId}`);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        
        this.sendMessage({
          type: 'init',
          document_id: docId
        });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type && this.listeners.has(data.type)) {
            this.listeners.get(data.type)?.forEach(listener => listener(data));
          }
          
          if (this.listeners.has('message')) {
            this.listeners.get('message')?.forEach(listener => listener(data));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket closed');
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Maximum reconnect attempts reached');
      return;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      if (this.docId) {
        this.connect(this.docId);
      }
    }, delay);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.docId = null;
    this.reconnectAttempts = 0;
  }

  sendMessage(message: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  sendFeedback(sectionId: string, feedbackType: 'continue' | 'edit', editedContent?: string): void {
    const feedback = {
      section_id: sectionId,
      feedback_type: feedbackType,
      edited_content: editedContent
    };
    
    this.sendMessage(feedback);
  }

  addEventListener(type: string, listener: WebSocketEventListener): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    
    this.listeners.get(type)?.push(listener);
  }

  removeEventListener(type: string, listener: WebSocketEventListener): void {
    if (!this.listeners.has(type)) {
      return;
    }
    
    const listeners = this.listeners.get(type);
    if (listeners) {
      this.listeners.set(
        type,
        listeners.filter(l => l !== listener)
      );
    }
  }
}

export const websocketService = new WebSocketService();