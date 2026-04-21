import { useEffect, useRef, useState } from 'react'

function fmtTime(iso) {
  const date = new Date(iso)
  return date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
}

export default function ChatWidget({ tgUserId }) {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [hasNew, setHasNew] = useState(false)
  const lastTs = useRef(null)
  const bottomRef = useRef(null)
  const messageCounter = useRef(-1)

  useEffect(() => {
    if (!tgUserId) return
    fetch(`/api/chat?telegram_user_id=${tgUserId}`)
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => {
        setMsgs(data)
        if (data.length) {
          lastTs.current = data[data.length - 1].created_at
        }
      })
      .catch(() => {})
  }, [tgUserId])

  useEffect(() => {
    if (!tgUserId) return undefined

    const intervalMs = open ? 8000 : 20000
    const timer = window.setInterval(() => {
      const since = lastTs.current || new Date(0).toISOString()
      fetch(`/api/chat?telegram_user_id=${tgUserId}&since=${encodeURIComponent(since)}`)
        .then((response) => (response.ok ? response.json() : []))
        .then((data) => {
          if (!data.length) return
          setMsgs((prev) => {
            const knownIds = new Set(prev.map((msg) => msg.id))
            const fresh = data.filter((msg) => !knownIds.has(msg.id))
            if (!fresh.length) return prev
            lastTs.current = fresh[fresh.length - 1].created_at
            if (!open && fresh.some((msg) => msg.direction === 'admin')) {
              setHasNew(true)
            }
            return [...prev, ...fresh]
          })
        })
        .catch(() => {})
    }, intervalMs)

    return () => window.clearInterval(timer)
  }, [open, tgUserId])

  useEffect(() => {
    if (!open) return
    setHasNew(false)
    window.setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 80)
  }, [open, msgs.length])

  function addSystemMsg(text) {
    const id = `sys_${messageCounter.current--}`
    setMsgs((prev) => [...prev, { id, content: text, direction: 'system', created_at: new Date().toISOString() }])
  }

  async function sendMessage() {
    if (!tgUserId || sending || !input.trim()) return
    const text = input.trim()
    setInput('')
    setSending(true)
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telegram_user_id: tgUserId, content: text }),
      })
      if (!response.ok) {
        addSystemMsg('⚠️ Не вдалося надіслати повідомлення. Спробуйте ще раз.')
        return
      }
      const message = await response.json()
      setMsgs((prev) => [...prev, message])
      lastTs.current = message.created_at
      addSystemMsg('📨 Повідомлення надіслано. Ми відповімо в цьому чаті.')
    } catch {
      addSystemMsg("⚠️ Мережева помилка. Перевірте з'єднання.")
    } finally {
      setSending(false)
    }
  }

  function onKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  if (!tgUserId) return null

  const realMsgs = msgs.filter((msg) => msg.direction !== 'system')

  return (
    <>
      <button className="chat-fab" onClick={() => setOpen(true)} type="button" aria-label="Відкрити чат">
        💬
        {hasNew && <span className="unread-dot" />}
      </button>

      {open && (
        <div className="chat-overlay" onClick={(event) => event.target === event.currentTarget && setOpen(false)}>
          <div className="chat-panel">
            <div className="chat-header">
              <div className="chat-avatar">🎣</div>
              <div className="chat-header-info">
                <div className="chat-header-title">Підтримка магазину</div>
                <div className="chat-header-sub">Пишіть щодо товарів, доставки або наявності</div>
              </div>
              <button className="chat-close" onClick={() => setOpen(false)} type="button" aria-label="Закрити чат">
                ✕
              </button>
            </div>

            <div className="chat-messages">
              {realMsgs.length === 0 && (
                <div className="chat-empty">
                  <div className="chat-empty-icon">💬</div>
                  <div className="chat-empty-title">Маєте питання?</div>
                  <div className="chat-empty-text">
                    Напишіть нам щодо товарів, кількості, доставки або самовивозу.
                  </div>
                </div>
              )}

              {msgs.map((msg) => {
                if (msg.direction === 'system') {
                  return (
                    <div key={msg.id} className="msg-system">
                      {msg.content}
                    </div>
                  )
                }

                return (
                  <div key={msg.id} className={`msg-row ${msg.direction}`}>
                    {msg.direction === 'admin' && <div className="msg-avatar">🎣</div>}
                    <div className={`msg-bubble ${msg.direction}`}>
                      <span className="msg-text">{msg.content}</span>
                      <span className="msg-time">{fmtTime(msg.created_at)}</span>
                    </div>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>

            <div className="chat-input-row">
              <textarea
                className="chat-textarea"
                rows={1}
                placeholder="Напишіть повідомлення…"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={onKeyDown}
                disabled={sending}
              />
              <button
                className="chat-send"
                onClick={sendMessage}
                disabled={sending || !input.trim()}
                type="button"
                aria-label="Надіслати"
              >
                {sending ? <span className="send-spin" /> : '➤'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
