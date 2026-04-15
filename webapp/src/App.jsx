import { useMemo, useState, useEffect, useRef, useCallback } from 'react'

/* ─── Product images (OLX CDN) ─── */
const IMAGES = [
  'https://ireland.apollo.olxcdn.com:443/v1/files/udyvz394go613-UA/image',
  'https://ireland.apollo.olxcdn.com:443/v1/files/zqaxpvx3vtku2-UA/image',
  'https://ireland.apollo.olxcdn.com:443/v1/files/n5t141bpaeb21-UA/image',
  'https://ireland.apollo.olxcdn.com:443/v1/files/iwmgbkyp39ep3-UA/image',
  'https://ireland.apollo.olxcdn.com:443/v1/files/18jxnbn1xd9y2-UA/image',
]

const FEATURES = [
  { icon: '🔔', text: 'Чутливий дзвіночковий механізм' },
  { icon: '⚖️', text: 'Регульоване навантаження (баласт)' },
  { icon: '🔩', text: 'Стандартне різьбове кріплення' },
  { icon: '🌙', text: 'Місце для хімічного світла' },
  { icon: '✅', text: 'Новий, готовий до використання' },
]

const DELIVERY = [
  { id: 'nova_poshta', icon: '🚚', label: 'Нова\nПошта' },
  { id: 'ukrposhta',  icon: '📦', label: 'Укр\nПошта' },
  { id: 'pickup',     icon: '🏪', label: 'Само\nвивіз' },
]

/* ─── Helpers ─── */
function useDebounce(val, ms) {
  const [dv, setDv] = useState(val)
  useEffect(() => {
    const t = setTimeout(() => setDv(val), ms)
    return () => clearTimeout(t)
  }, [val, ms])
  return dv
}

function fmtTime(iso) {
  const d = new Date(iso)
  return d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
}

function validate(cart, form, dlv) {
  if (!Object.values(cart).some(q => q > 0)) return '🛒 Додайте хоча б один товар'
  if (form.name.trim().length < 2)            return "Вкажіть ваше ім'я та прізвище"
  if (!/^\+?[\d\s\-(]{7,}/.test(form.phone.trim())) return 'Перевірте номер телефону'
  if (dlv.method === 'nova_poshta') {
    if (!dlv.np.cityRef)      return 'Оберіть місто доставки (Нова Пошта)'
    if (!dlv.np.warehouseRef) return 'Оберіть відділення або поштомат'
  }
  if (dlv.method === 'ukrposhta') {
    if (dlv.up.city.trim().length < 2)   return 'Вкажіть місто (Укрпошта)'
    if (dlv.up.branch.trim().length < 1) return 'Вкажіть номер відділення'
  }
  return null
}

/* ─── Gallery ─── */
function Gallery({ images }) {
  const [idx, setIdx]   = useState(0)
  const startX = useRef(null)

  const prev = () => setIdx(i => (i - 1 + images.length) % images.length)
  const next = () => setIdx(i => (i + 1) % images.length)

  const onTouchStart = e => { startX.current = e.touches[0].clientX }
  const onTouchEnd   = e => {
    if (startX.current === null) return
    const dx = e.changedTouches[0].clientX - startX.current
    if (dx > 50)  prev()
    if (dx < -50) next()
    startX.current = null
  }

  return (
    <div className="gallery" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
      <div className="gallery-track" style={{ transform: `translateX(-${idx * 100}%)` }}>
        {images.map((src, i) => (
          <div key={i} className="gallery-slide">
            <img src={src} alt={`Фото ${i + 1}`} loading={i === 0 ? 'eager' : 'lazy'} />
          </div>
        ))}
      </div>
      {images.length > 1 && (
        <>
          <button className="gallery-arrow prev" onClick={prev}>‹</button>
          <button className="gallery-arrow next" onClick={next}>›</button>
          <div className="gallery-dots">
            {images.map((_, i) => (
              <button key={i} className={`gallery-dot${i === idx ? ' on' : ''}`} onClick={() => setIdx(i)} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

/* ─── Chat Widget ─── */
function ChatWidget({ tgUserId }) {
  const [open,     setOpen]    = useState(false)
  const [msgs,     setMsgs]    = useState([])
  const [input,    setInput]   = useState('')
  const [sending,  setSending] = useState(false)
  const [hasNew,   setHasNew]  = useState(false)
  const lastTs = useRef(null)
  const bottomRef = useRef(null)
  const pollRef   = useRef(null)

  /* Initial load */
  useEffect(() => {
    if (!tgUserId) return
    fetch(`/api/chat?telegram_user_id=${tgUserId}`)
      .then(r => r.ok ? r.json() : [])
      .then(data => {
        setMsgs(data)
        if (data.length) lastTs.current = data[data.length - 1].created_at
      })
      .catch(() => {})
  }, [tgUserId])

  /* Poll for new messages every 8s */
  useEffect(() => {
    if (!tgUserId) return
    pollRef.current = setInterval(() => {
      const since = lastTs.current || new Date(0).toISOString()
      fetch(`/api/chat?telegram_user_id=${tgUserId}&since=${encodeURIComponent(since)}`)
        .then(r => r.ok ? r.json() : [])
        .then(data => {
          if (!data.length) return
          setMsgs(prev => {
            const ids = new Set(prev.map(m => m.id))
            const fresh = data.filter(m => !ids.has(m.id))
            if (!fresh.length) return prev
            lastTs.current = fresh[fresh.length - 1].created_at
            if (fresh.some(m => m.direction === 'admin') && !open) setHasNew(true)
            return [...prev, ...fresh]
          })
        })
        .catch(() => {})
    }, 8000)
    return () => clearInterval(pollRef.current)
  }, [tgUserId, open])

  /* Scroll to bottom when opened or new messages */
  useEffect(() => {
    if (open) {
      setHasNew(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 60)
    }
  }, [open, msgs.length])

  async function sendMsg() {
    if (!input.trim() || sending || !tgUserId) return
    const text = input.trim()
    setInput('')
    setSending(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telegram_user_id: tgUserId, content: text }),
      })
      if (res.ok) {
        const msg = await res.json()
        setMsgs(prev => [...prev, msg])
        lastTs.current = msg.created_at
      }
    } catch (e) { /* ignore */ }
    finally { setSending(false) }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg() }
  }

  if (!tgUserId) return null

  return (
    <>
      <button className="chat-fab" onClick={() => setOpen(true)}>
        💬
        {hasNew && <span className="unread-dot" />}
      </button>

      {open && (
        <div className="chat-overlay" onClick={e => e.target === e.currentTarget && setOpen(false)}>
          <div className="chat-panel">
            <div className="chat-header">
              <div className="chat-header-info">
                <div className="chat-header-title">💬 Підтримка</div>
                <div className="chat-header-sub">Зазвичай відповідаємо протягом години</div>
              </div>
              <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
            </div>

            <div className="chat-messages">
              {msgs.map(m => (
                <div key={m.id} style={{ display: 'flex', flexDirection: 'column',
                  alignItems: m.direction === 'user' ? 'flex-end' : 'flex-start' }}>
                  <div className={`msg-bubble ${m.direction}`}>
                    {m.content}
                    <span className="msg-time">{fmtTime(m.created_at)}</span>
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="chat-input-row">
              <textarea
                className="chat-textarea"
                rows={1}
                placeholder="Напишіть повідомлення…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKeyDown}
              />
              <button className="chat-send" onClick={sendMsg} disabled={!input.trim() || sending}>
                {sending ? '…' : '➤'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

/* ═══════════════════════ Main App ═══════════════════════ */
export default function App() {
  const tg     = window.Telegram?.WebApp
  const tgUser = tg?.initDataUnsafe?.user

  useEffect(() => { if (tg) { tg.ready(); tg.expand() } }, [])

  /* qty */
  const SKU = 'signal_fishing'
  const PRICE = 120
  const [qty, setQty] = useState(0)
  const total = qty * PRICE

  /* form */
  const [form, setForm] = useState({ name: '', phone: '' })

  /* delivery */
  const [dlv, setDlv] = useState({
    method: 'nova_poshta',
    np: { cityName: '', cityRef: '', warehouseName: '', warehouseRef: '' },
    up: { city: '', branch: '', index: '' },
  })

  /* NP autocomplete */
  const [cityQ,    setCityQ]    = useState('')
  const [cityList, setCityList] = useState([])
  const [cityBusy, setCityBusy] = useState(false)
  const [whQ,      setWhQ]      = useState('')
  const [whList,   setWhList]   = useState([])
  const [whBusy,   setWhBusy]   = useState(false)
  const dCityQ = useDebounce(cityQ, 380)
  const dWhQ   = useDebounce(whQ,   350)

  useEffect(() => {
    if (dlv.method !== 'nova_poshta') return
    if (dlv.np.cityRef || dCityQ.length < 2) { setCityList([]); return }
    let alive = true; setCityBusy(true)
    fetch(`/api/np/cities?query=${encodeURIComponent(dCityQ)}`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => { if (alive) setCityList((d.items || []).slice(0, 8)) })
      .catch(() => { if (alive) setCityList([]) })
      .finally(() => { if (alive) setCityBusy(false) })
    return () => { alive = false }
  }, [dCityQ, dlv.np.cityRef, dlv.method])

  useEffect(() => {
    if (!dlv.np.cityRef) { setWhList([]); return }
    let alive = true; setWhBusy(true)
    const q = dWhQ ? `&query=${encodeURIComponent(dWhQ)}` : ''
    fetch(`/api/np/warehouses?city_ref=${dlv.np.cityRef}${q}`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => { if (alive) setWhList((d.items || []).slice(0, 12)) })
      .catch(() => { if (alive) setWhList([]) })
      .finally(() => { if (alive) setWhBusy(false) })
    return () => { alive = false }
  }, [dlv.np.cityRef, dWhQ])

  function pickCity(c) {
    const ref = c.DeliveryCity || c.Ref, name = c.Present || c.MainDescription
    setDlv(p => ({ ...p, np: { cityName: name, cityRef: ref, warehouseName: '', warehouseRef: '' } }))
    setCityQ(name); setCityList([]); setWhQ(''); setWhList([])
  }
  function clearCity() {
    setDlv(p => ({ ...p, np: { cityName:'', cityRef:'', warehouseName:'', warehouseRef:'' } }))
    setCityQ(''); setCityList([]); setWhQ(''); setWhList([])
  }
  function pickWarehouse(w) {
    setDlv(p => ({ ...p, np: { ...p.np, warehouseName: w.Description, warehouseRef: w.Ref } }))
    setWhQ(w.Description); setWhList([])
  }
  function clearWarehouse() {
    setDlv(p => ({ ...p, np: { ...p.np, warehouseName: '', warehouseRef: '' } }))
    setWhQ(''); setWhList([])
  }

  /* submit */
  const [status,  setStatus]  = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit() {
    const fakeCart = qty > 0 ? { [SKU]: qty } : {}
    const err = validate(fakeCart, form, dlv)
    if (err) { setStatus({ ok: false, text: err }); return }
    if (!tgUser?.id) {
      setStatus({ ok: false, text: 'Відкрийте магазин через кнопку в боті' }); return
    }

    let deliveryInfo, npPayload = null
    if (dlv.method === 'nova_poshta') {
      deliveryInfo = `Нова Пошта: ${dlv.np.cityName}, ${dlv.np.warehouseName}`
      npPayload = { city_name: dlv.np.cityName, warehouse_name: dlv.np.warehouseName,
        city_ref: dlv.np.cityRef || null, warehouse_ref: dlv.np.warehouseRef || null }
    } else if (dlv.method === 'ukrposhta') {
      deliveryInfo = `Укрпошта: ${dlv.up.city}, відд. №${dlv.up.branch}` +
        (dlv.up.index ? `, індекс ${dlv.up.index}` : '')
    } else {
      deliveryInfo = 'Самовивіз'
    }

    setLoading(true); setStatus(null)
    try {
      const res = await fetch('/api/orders', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer: { name: form.name.trim(), phone: form.phone.trim(), delivery_info: deliveryInfo },
          items: [{ sku: SKU, qty, price: PRICE }],
          meta: { source_code: tg?.initDataUnsafe?.start_param || null,
            webapp_version: 'v3', delivery_method: dlv.method },
          nova_poshta: npPayload,
          telegram_user_id: tgUser.id,
          telegram_username: tgUser.username || null,
        }),
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({}))
        setStatus({ ok: false, text: `Помилка: ${e.detail || res.status}` }); return
      }
      const data = await res.json()
      setStatus({ ok: true,
        text: `✅ Замовлення #${data.order_uuid.slice(0, 8)} прийнято!\nОчікуйте повідомлення від бота.` })
      setTimeout(() => tg?.close(), 2500)
    } catch (e) {
      setStatus({ ok: false, text: `Мережева помилка: ${e.message}` })
    } finally { setLoading(false) }
  }

  /* ─── Render ─── */
  return (
    <>
      <div className="wrap">
        {/* ── Gallery ── */}
        <Gallery images={IMAGES} />

        {/* ── Product info ── */}
        <div className="product-info-block">
          <div className="product-badge-row">
            <span className="badge-hit">⭐ ХІТ</span>
            <span className="badge-new">Новий</span>
          </div>
          <div className="product-title-big">Сигналізатор клювання механічний</div>
          <div className="product-price-big">120 ₴</div>
          <div className="product-features">
            {FEATURES.map((f, i) => (
              <div key={i} className="feature-item">
                <span className="feature-icon">{f.icon}</span>
                <span>{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Qty ── */}
        <div className="sec-label">Кількість</div>
        <div className="qty-card">
          <div className="qty-card-info">
            <div className="qty-card-name">🎣 Сигналізатор клювання</div>
            <div className="qty-card-price">{PRICE} ₴ за шт.</div>
          </div>
          <div className="qty">
            <button className="qty-btn" onClick={() => setQty(q => Math.max(0, q - 1))} disabled={qty === 0}>−</button>
            <span className="qty-num">{qty}</span>
            <button className="qty-btn" onClick={() => setQty(q => q + 1)}>+</button>
          </div>
        </div>

        {/* ── Delivery tabs ── */}
        <div className="sec-label">Доставка</div>
        <div className="dlv-wrap">
          <div className="dlv-tabs">
            {DELIVERY.map(t => (
              <button key={t.id}
                className={`dlv-tab${dlv.method === t.id ? ' on' : ''}`}
                onClick={() => setDlv(p => ({ ...p, method: t.id }))}>
                {t.icon}<br />{t.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Nova Poshta ── */}
        {dlv.method === 'nova_poshta' && (
          <div className="card">
            <div className="form-inner">
              <div className="f-row">
                <label className="f-lbl">Місто</label>
                {dlv.np.cityRef ? (
                  <div className="sel-val">
                    <span className="sel-check">✓</span>
                    <span style={{flex:1,fontSize:14}}>{dlv.np.cityName}</span>
                    <button className="sel-change" onClick={clearCity}>Змінити</button>
                  </div>
                ) : (
                  <div className="inp-wrap">
                    <input className="f-inp" placeholder="Введіть місто…"
                      value={cityQ} onChange={e => setCityQ(e.target.value)} />
                    {cityBusy && <div className="inp-spin" />}
                    {cityList.length > 0 && (
                      <div className="dropdown">
                        {cityList.map((c, i) => (
                          <div key={i} className="dd-item" onClick={() => pickCity(c)}>
                            <div className="dd-main">{c.MainDescription}</div>
                            <div className="dd-sub">{c.AreaDescription ? `${c.AreaDescription} обл.` : c.Present}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {dCityQ.length >= 2 && !cityBusy && cityList.length === 0 && (
                      <div className="dropdown"><div className="dd-empty">Нічого не знайдено</div></div>
                    )}
                  </div>
                )}
              </div>
              {dlv.np.cityRef && (
                <div className="f-row">
                  <label className="f-lbl">Відділення / Поштомат</label>
                  {dlv.np.warehouseRef ? (
                    <div className="sel-val">
                      <span className="sel-check">✓</span>
                      <span style={{flex:1,fontSize:13,lineHeight:1.3}}>{dlv.np.warehouseName}</span>
                      <button className="sel-change" onClick={clearWarehouse}>Змінити</button>
                    </div>
                  ) : (
                    <div className="inp-wrap">
                      <input className="f-inp" placeholder="Пошук відділення або поштомату…"
                        value={whQ} onChange={e => setWhQ(e.target.value)} />
                      {whBusy && <div className="inp-spin" />}
                      {whList.length > 0 && (
                        <div className="dropdown">
                          {whList.map((w, i) => (
                            <div key={i} className="dd-item" onClick={() => pickWarehouse(w)}>
                              <div className="dd-main">{w.Description}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Укрпошта ── */}
        {dlv.method === 'ukrposhta' && (
          <div className="card">
            <div className="form-inner">
              <div className="f-row">
                <label className="f-lbl">Місто</label>
                <input className="f-inp" placeholder="Наприклад: Хмельницький"
                  value={dlv.up.city}
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, city: e.target.value } }))} />
              </div>
              <div className="f-row">
                <label className="f-lbl">Номер відділення</label>
                <input className="f-inp" placeholder="Наприклад: 12" type="tel"
                  value={dlv.up.branch}
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, branch: e.target.value } }))} />
              </div>
              <div className="f-row">
                <label className="f-lbl">Поштовий індекс (необов'язково)</label>
                <input className="f-inp" placeholder="29000" type="tel"
                  value={dlv.up.index}
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, index: e.target.value } }))} />
              </div>
            </div>
          </div>
        )}

        {/* ── Самовивіз ── */}
        {dlv.method === 'pickup' && (
          <div className="card">
            <div className="tip">
              <span className="tip-icon">ℹ️</span>
              <span>Самовивіз узгоджується індивідуально. Після замовлення ми зв'яжемось для уточнення адреси та часу.</span>
            </div>
          </div>
        )}

        {/* ── Ваші дані ── */}
        <div className="sec-label">Ваші дані</div>
        <div className="card">
          <div className="form-inner">
            <div className="f-row">
              <label className="f-lbl">Ім'я та прізвище</label>
              <input className="f-inp" placeholder="Іваненко Іван Іванович"
                value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
            </div>
            <div className="f-row">
              <label className="f-lbl">Номер телефону</label>
              <input className="f-inp" type="tel" placeholder="+38 (0__) ___-__-__"
                value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} />
            </div>
          </div>
        </div>

        {/* ── Замовлення ── */}
        {qty > 0 && (
          <>
            <div className="sec-label">Ваше замовлення</div>
            <div className="card">
              <div className="sum-row">
                <span className="sum-lbl">🎣 Сигналізатор × {qty}</span>
                <span className="sum-val">{total} ₴</span>
              </div>
              <div className="sum-row">
                <span className="sum-ttl">💰 Разом</span>
                <span className="sum-ttl-v">{total} ₴</span>
              </div>
            </div>
          </>
        )}

        {/* Status */}
        {status && (
          <div className={`status ${status.ok ? 's-ok' : 's-err'}`}>{status.text}</div>
        )}
      </div>

      {/* Chat */}
      <ChatWidget tgUserId={tgUser?.id} />

      {/* Footer */}
      <div className="footer">
        <button className="submit-btn" onClick={submit} disabled={loading || qty === 0}>
          {loading ? '⏳ Відправляємо…' : qty === 0 ? 'Оберіть кількість' : `Замовити · ${total} ₴`}
        </button>
      </div>
    </>
  )
}
