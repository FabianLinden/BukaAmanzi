import { useEffect, useRef, useCallback } from 'react';

type WebSocketMessage = {
  action: string;
  entity_type?: string;
  [key: string]: any;
};

type WebSocketCallbacks = {
  onOpen?: (event: Event) => void;
  onMessage: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
};

export const useWebSocket = (url: string, callbacks: WebSocketCallbacks) => {
  const ws = useRef<WebSocket | null>(null);
  const { onMessage, onOpen, onClose, onError } = callbacks;

  const send = useCallback((message: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    // Create WebSocket connection
    const socket = new WebSocket(url);
    ws.current = socket;

    // Set up event listeners
    if (onOpen) {
      socket.addEventListener('open', onOpen);
    }

    socket.addEventListener('message', onMessage);

    if (onClose) {
      socket.addEventListener('close', onClose);
    }

    if (onError) {
      socket.addEventListener('error', onError);
    }

    // Clean up on unmount
    return () => {
      if (onOpen) {
        socket.removeEventListener('open', onOpen);
      }
      socket.removeEventListener('message', onMessage);
      if (onClose) {
        socket.removeEventListener('close', onClose);
      }
      if (onError) {
        socket.removeEventListener('error', onError);
      }
      socket.close();
    };
  }, [url, onOpen, onMessage, onClose, onError]);

  return { send };
};

export default useWebSocket;