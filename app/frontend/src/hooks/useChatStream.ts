import { useCallback, useRef, useState } from 'react'

export interface Citation {
  id: string
  title: string
  source: string
  score: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  crisis?: boolean
  status?: string
}

function getSessionId(): string {
  const key = 'steady-mind-session'
  let id = localStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(key, id)
  }
  return id
}

export function useChatStream(lang: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    newSessionId()
    setMessages([])
    setStreaming(false)
  }, [])

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || streaming) return

      setMessages((prev) => [...prev, { role: 'user', content: text }])
      setStreaming(true)

      const citations: Citation[] = []
      let assistantText = ''
      abortRef.current = new AbortController()

      setMessages((prev) => [...prev, { role: 'assistant', content: '', citations: [], status: '檢索相關文獻中…' }])

      const patchAssistant = (patch: Partial<ChatMessage>) => {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant') {
            next[next.length - 1] = { ...last, ...patch }
          }
          return next
        })
      }

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: getSessionId(),
            message: text,
            lang,
          }),
          signal: abortRef.current.signal,
        })

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`)
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        const processPart = (part: string) => {
          const block = part.trim()
          if (!block) return
          const lines = block.split('\n')
          let event = 'message'
          let data = ''
          for (const line of lines) {
            if (line.startsWith('event:')) event = line.slice(6).trim()
            if (line.startsWith('data:')) data = line.slice(5).trim()
          }
          if (!data) return

          const parsed = JSON.parse(data)
          if (event === 'token') {
            assistantText += parsed.text
            patchAssistant({ content: assistantText, citations: [...citations], status: undefined })
          } else if (event === 'citation') {
            citations.push(parsed)
            patchAssistant({
              citations: [...citations],
              status: `已找到 ${citations.length} 則文獻…`,
            })
          } else if (event === 'status') {
            patchAssistant({ status: parsed.message })
          } else if (event === 'crisis') {
            patchAssistant({ content: parsed.message, crisis: true, status: undefined })
          } else if (event === 'done') {
            patchAssistant({ content: assistantText, citations: [...citations], status: undefined })
          }
        }

        while (true) {
          const { done, value } = await reader.read()
          if (value) {
            buffer += decoder.decode(value, { stream: true })
            buffer = buffer.replace(/\r\n/g, '\n')
            const parts = buffer.split('\n\n')
            buffer = parts.pop() ?? ''
            for (const part of parts) processPart(part)
          }
          if (done) {
            if (buffer.trim()) processPart(buffer)
            break
          }
        }

        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant' && !last.crisis) {
            next[next.length - 1] = { ...last, content: assistantText, citations }
          }
          return next
        })
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setMessages((prev) => {
            const next = [...prev]
            next[next.length - 1] = {
              role: 'assistant',
              content:
                import.meta.env.VITE_DEMO_MODE === 'true'
                  ? '連線失敗，請稍後再試。'
                  : '連線失敗。請確認後端已啟動（make serve）。',
            }
            return next
          })
        }
      } finally {
        setStreaming(false)
      }
    },
    [lang, streaming],
  )

  return { messages, streaming, send, reset }
}

export function newSessionId(): string {
  const id = crypto.randomUUID()
  localStorage.setItem('steady-mind-session', id)
  return id
}
