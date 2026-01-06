import { useState, useEffect, useRef } from 'react';

export interface Tick {
  symbol: string;
  price: number;
  timestamp: string | number;
}

export const useStreamingData = (url: string) => {
  const [data, setData] = useState<Tick[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData((prev) => [...prev, message].slice(-50)); // Keep last 50
    };

    return () => {
      ws.current?.close();
    };
  }, [url]);

  return data;
};
