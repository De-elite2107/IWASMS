import { useEffect, useRef, useCallback, useState } from 'react'
import { useAppSelector } from './useStore'
import type { SecurityEvent } from '../types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/events/'

export function useSecurityEventStream(onEvent: (event: SecurityEvent) => void) {
  const token = useAppSelector((state) => state.auth.access)
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectDelay = useRef(1000)
  const onEventRef = useRef(onEvent)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  const connect = useCallback(() => {
    if (!token) return

    // Close existing connection
    if (socketRef.current) {
      socketRef.current.close(1000)
    }

    const url = `${WS_URL}?token=${token}`
    const ws = new WebSocket(url)

    ws.onopen = () => {
      reconnectDelay.current = 1000
      setIsConnected(true)
      console.log('[WS] Connected to security event stream')
    }

    ws.onmessage = (msg) => {
      try {
        const event: SecurityEvent = JSON.parse(msg.data)
        onEventRef.current(event)
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    ws.onclose = (e) => {
      setIsConnected(false)
      console.log(`[WS] Disconnected (code=${e.code}). Reconnecting in ${reconnectDelay.current}ms`)
      if (e.code !== 1000) {
        // Only reconnect if not intentionally closed
        setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000)
          connect()
        }, reconnectDelay.current)
      }
    }

    ws.onerror = () => {
      setIsConnected(false)
    }

    socketRef.current = ws
  }, [token])

  useEffect(() => {
    connect()
    return () => {
      socketRef.current?.close(1000, 'component unmounted')
      socketRef.current = null
    }
  }, [connect])

  return { isConnected }
}
