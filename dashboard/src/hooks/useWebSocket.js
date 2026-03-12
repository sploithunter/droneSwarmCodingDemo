import { useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../utils/constants';

export default function useWebSocket(dispatch) {
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const backoffRef = useRef(1000);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      dispatch({ type: 'SET_CONNECTED', payload: true });
      backoffRef.current = 1000;
    };

    ws.onclose = () => {
      dispatch({ type: 'SET_CONNECTED', payload: false });
      // Auto-reconnect with backoff
      reconnectRef.current = setTimeout(() => {
        backoffRef.current = Math.min(backoffRef.current * 2, 30000);
        connect();
      }, backoffRef.current);
    };

    ws.onerror = () => {};

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
          case 'drone_state_batch':
            dispatch({ type: 'DRONE_STATE_BATCH', payload: msg });
            break;
          case 'drone_alert':
            dispatch({ type: 'DRONE_ALERT', payload: msg.data });
            break;
          case 'mission_plan':
            dispatch({ type: 'MISSION_PLAN', payload: msg.data });
            break;
          case 'swarm_summary':
            dispatch({ type: 'SWARM_SUMMARY', payload: msg.data });
            break;
        }
      } catch (e) {}
    };

    wsRef.current = ws;
  }, [dispatch]);

  useEffect(() => {
    let cancelled = false;

    // Delay connection slightly so StrictMode cleanup can cancel before the socket opens
    const timer = setTimeout(() => {
      if (!cancelled) connect();
    }, 0);

    return () => {
      cancelled = true;
      clearTimeout(timer);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return wsRef;
}
