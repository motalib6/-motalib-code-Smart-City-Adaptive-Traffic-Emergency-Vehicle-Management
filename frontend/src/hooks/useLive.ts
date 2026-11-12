
import { useEffect, useState } from 'react';
import { liveSocket, type WsStatus } from '../services/websocket';
import type { LiveEvent } from '../types';

export function useLiveSocket(onEvent?: (ev: LiveEvent) => void) {
  const [status, setStatus] = useState<WsStatus>(liveSocket.status);
  useEffect(() => {
    const offStatus = liveSocket.onStatus(setStatus);
    const offEvent = onEvent ? liveSocket.onEvent(onEvent) : () => undefined;
    liveSocket.connect();
    return () => { offStatus(); offEvent(); liveSocket.disconnect(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return status;
}
