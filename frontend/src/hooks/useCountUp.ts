import { useEffect, useRef, useState } from 'react'

/**
 * Animates a number from 0 to `target` over `duration` ms.
 */
export function useCountUp(target: number, duration = 800): number {
  const [value, setValue] = useState(0)
  const frameRef = useRef<number>()
  const startRef = useRef<number>()
  const startValueRef = useRef(0)

  useEffect(() => {
    startRef.current = undefined
    startValueRef.current = value

    const animate = (timestamp: number) => {
      if (!startRef.current) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(startValueRef.current + (target - startValueRef.current) * eased))
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      }
    }

    frameRef.current = requestAnimationFrame(animate)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration])

  return value
}
