import { useMemo, useState, useEffect } from 'react'

/* ─── Catalog ─── */
const CATALOG = [
  {
    sku:   'signal_fishing',
    title: 'Сигналізатор клювання',
    desc:  'Механічний • Чутливий дзвіночок • Регульоване навантаження • Стандартне різьбове кріплення • Місце для хімсвітла',
    price: 120,
    icon:  '🎣',
    badge: 'ХІТ',
  },
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

/* ─── App ─── */
export default function App() {
  const tg     = window.Telegram?.WebApp
  const tgUser = tg?.initDataUnsafe?.user

  useEffect(() => { if (tg) { tg.ready(); tg.expand() } }, [])

  /* cart */
  const [cart, setCart] = useState({})
  const qty     = sku => cart[sku] || 0
  const addOne  = sku => setCart(p => ({ ...p, [sku]: (p[sku] || 0) + 1 }))
  const subOne  = sku => setCart(p => ({ ...p, [sku]: Math.max(0, (p[sku] || 0) - 1) }))
  const total     = useMemo(() => CATALOG.reduce((s, p) => s + qty(p.sku) * p.price, 0), [cart])
  const cartCount = useMemo(() => Object.values(cart).reduce((s, q) => s + q, 0), [cart])

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

  /* fetch cities */
  useEffect(() => {
    if (dlv.method !== 'nova_poshta') return
    if (dlv.np.cityRef || dCityQ.length < 2) { setCityList([]); return }
    let alive = true
    setCityBusy(true)
    fetch(`/api/np/cities?query=${encodeURIComponent(dCityQ)}`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => { if (alive) setCityList((d.items || []).slice(0, 8)) })
      .catch(() => { if (alive) setCityList([]) })
      .finally(() => { if (alive) setCityBusy(false) })
    return () => { alive = false }
  }, [dCityQ, dlv.np.cityRef, dlv.method])

  /* fetch warehouses */
  useEffect(() => {
    if (!dlv.np.cityRef) { setWhList([]); return }
    let alive = true
    setWhBusy(true)
    const q = dWhQ ? `&query=${encodeURIComponent(dWhQ)}` : ''
    fetch(`/api/np/warehouses?city_ref=${dlv.np.cityRef}${q}`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => { if (alive) setWhList((d.items || []).slice(0, 12)) })
      .catch(() => { if (alive) setWhList([]) })
      .finally(() => { if (alive) setWhBusy(false) })
    return () => { alive = false }
  }, [dlv.np.cityRef, dWhQ])

  function pickCity(c) {
    const ref  = c.DeliveryCity || c.Ref
    const name = c.Present || c.MainDescription
    setDlv(p => ({ ...p, np: { cityName: name, cityRef: ref, warehouseName: '', warehouseRef: '' } }))
    setCityQ(name); setCityList([])
    setWhQ('');     setWhList([])
  }
  function clearCity() {
    setDlv(p => ({ ...p, np: { cityName: '', cityRef: '', warehouseName: '', warehouseRef: '' } }))
    setCityQ(''); setCityList([])
    setWhQ('');   setWhList([])
  }
  function pickWarehouse(w) {
    setDlv(p => ({ ...p, np: { ...p.np, warehouseName: w.Description, warehouseRef: w.Ref } }))
    setWhQ(w.Description); setWhList([])
  }
  function clearWarehouse() {
    setDlv(p => ({ ...p, np: { ...p.np, warehouseName: '', warehouseRef: '' } }))
    setWhQ(''); setWhList([])
  }

  /* submission */
  const [status,  setStatus]  = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit() {
    const err = validate(cart, form, dlv)
    if (err) { setStatus({ ok: false, text: err }); return }
    if (!tgUser?.id) {
      setStatus({ ok: false, text: 'Відкрийте магазин через кнопку в боті' })
      return
    }

    const items = CATALOG.filter(p => qty(p.sku) > 0)
      .map(p => ({ sku: p.sku, qty: qty(p.sku), price: p.price }))

    let deliveryInfo, npPayload = null

    if (dlv.method === 'nova_poshta') {
      deliveryInfo = `Нова Пошта: ${dlv.np.cityName}, ${dlv.np.warehouseName}`
      npPayload = {
        city_name:      dlv.np.cityName,
        warehouse_name: dlv.np.warehouseName,
        city_ref:       dlv.np.cityRef      || null,
        warehouse_ref:  dlv.np.warehouseRef || null,
      }
    } else if (dlv.method === 'ukrposhta') {
      deliveryInfo = `Укрпошта: ${dlv.up.city}, відд. №${dlv.up.branch}` +
        (dlv.up.index ? `, індекс ${dlv.up.index}` : '')
    } else {
      deliveryInfo = 'Самовивіз'
    }

    setLoading(true); setStatus(null)
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer: {
            name:          form.name.trim(),
            phone:         form.phone.trim(),
            delivery_info: deliveryInfo,
          },
          items,
          meta: {
            source_code:     tg?.initDataUnsafe?.start_param || null,
            webapp_version:  'v2',
            delivery_method: dlv.method,
          },
          nova_poshta:       npPayload,
          telegram_user_id:  tgUser.id,
          telegram_username: tgUser.username || null,
        }),
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({}))
        setStatus({ ok: false, text: `Помилка: ${e.detail || res.status}` })
        return
      }
      const data = await res.json()
      setStatus({
        ok: true,
        text: `✅ Замовлення #${data.order_uuid.slice(0, 8)} прийнято!\nОчікуйте повідомлення від бота.`,
      })
      setTimeout(() => tg?.close(), 2500)
    } catch (e) {
      setStatus({ ok: false, text: `Мережева помилка: ${e.message}` })
    } finally {
      setLoading(false)
    }
  }

  /* ─── Render ─── */
  return (
    <>
      <div className="wrap">
        {/* Header */}
        <div className="app-header">
          <div className="app-title">🛒 Магазин</div>
          {cartCount > 0 && (
            <div className="cart-pill">🛍 {cartCount} · {total} ₴</div>
          )}
        </div>

        {/* ── Каталог ── */}
        <div className="sec-label">Товари</div>
        <div className="card">
          {CATALOG.map(p => (
            <div key={p.sku} className="prod-row">
              <div className="prod-icon">{p.icon}</div>
              <div className="prod-body">
                <div className="prod-name">
                  {p.title}
                  {p.badge && <span className="prod-badge">{p.badge}</span>}
                </div>
                <div className="prod-desc">{p.desc}</div>
                <div className="prod-price">{p.price} ₴</div>
              </div>
              <div className="qty">
                <button className="qty-btn" onClick={() => subOne(p.sku)} disabled={qty(p.sku) === 0}>−</button>
                <span className="qty-num">{qty(p.sku)}</span>
                <button className="qty-btn" onClick={() => addOne(p.sku)}>+</button>
              </div>
            </div>
          ))}
        </div>

        {/* ── Доставка: таби ── */}
        <div className="sec-label">Доставка</div>
        <div className="dlv-tabs">
          {DELIVERY.map(t => (
            <button
              key={t.id}
              className={`dlv-tab${dlv.method === t.id ? ' on' : ''}`}
              onClick={() => setDlv(p => ({ ...p, method: t.id }))}
            >
              {t.icon}<br />{t.label}
            </button>
          ))}
        </div>

        {/* ── Нова Пошта ── */}
        {dlv.method === 'nova_poshta' && (
          <div className="card">
            <div className="form-inner">
              {/* City */}
              <div className="f-row">
                <label className="f-lbl">Місто</label>
                {dlv.np.cityRef ? (
                  <div className="sel-val">
                    <span className="sel-check">✓</span>
                    <span style={{ flex: 1, fontSize: 14 }}>{dlv.np.cityName}</span>
                    <button className="sel-change" onClick={clearCity}>Змінити</button>
                  </div>
                ) : (
                  <div className="inp-wrap">
                    <input
                      className="f-inp"
                      placeholder="Введіть назву міста…"
                      value={cityQ}
                      onChange={e => setCityQ(e.target.value)}
                    />
                    {cityBusy && <div className="inp-spin" />}
                    {cityList.length > 0 && (
                      <div className="dropdown">
                        {cityList.map((c, i) => (
                          <div key={i} className="dd-item" onClick={() => pickCity(c)}>
                            <div className="dd-main">{c.MainDescription}</div>
                            <div className="dd-sub">
                              {c.AreaDescription ? `${c.AreaDescription} обл.` : c.Present}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {dCityQ.length >= 2 && !cityBusy && cityList.length === 0 && (
                      <div className="dropdown">
                        <div className="dd-empty">Нічого не знайдено</div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Warehouse (after city chosen) */}
              {dlv.np.cityRef && (
                <div className="f-row">
                  <label className="f-lbl">Відділення / Поштомат</label>
                  {dlv.np.warehouseRef ? (
                    <div className="sel-val">
                      <span className="sel-check">✓</span>
                      <span style={{ flex: 1, fontSize: 13, lineHeight: 1.3 }}>{dlv.np.warehouseName}</span>
                      <button className="sel-change" onClick={clearWarehouse}>Змінити</button>
                    </div>
                  ) : (
                    <div className="inp-wrap">
                      <input
                        className="f-inp"
                        placeholder="Пошук відділення або поштомату…"
                        value={whQ}
                        onChange={e => setWhQ(e.target.value)}
                      />
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
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, city: e.target.value } }))}
                />
              </div>
              <div className="f-row">
                <label className="f-lbl">Номер відділення</label>
                <input className="f-inp" placeholder="Наприклад: 12" type="tel"
                  value={dlv.up.branch}
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, branch: e.target.value } }))}
                />
              </div>
              <div className="f-row">
                <label className="f-lbl">Поштовий індекс (необов'язково)</label>
                <input className="f-inp" placeholder="Наприклад: 29000" type="tel"
                  value={dlv.up.index}
                  onChange={e => setDlv(p => ({ ...p, up: { ...p.up, index: e.target.value } }))}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Самовивіз ── */}
        {dlv.method === 'pickup' && (
          <div className="card">
            <div className="tip">
              <span className="tip-icon">ℹ️</span>
              <span>
                Самовивіз узгоджується індивідуально. Після підтвердження
                замовлення ми зв'яжемось з вами для уточнення деталей та адреси.
              </span>
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
                value={form.name}
                onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div className="f-row">
              <label className="f-lbl">Номер телефону</label>
              <input className="f-inp" type="tel" placeholder="+38 (0__) ___-__-__"
                value={form.phone}
                onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
              />
            </div>
          </div>
        </div>

        {/* ── Кошик ── */}
        {cartCount > 0 && (
          <>
            <div className="sec-label">Ваше замовлення</div>
            <div className="card">
              {CATALOG.filter(p => qty(p.sku) > 0).map(p => (
                <div key={p.sku} className="sum-row">
                  <span className="sum-lbl">{p.icon} {p.title} × {qty(p.sku)}</span>
                  <span className="sum-val">{qty(p.sku) * p.price} ₴</span>
                </div>
              ))}
              <div className="sum-row">
                <span className="sum-ttl-l">💰 Разом</span>
                <span className="sum-ttl-v">{total} ₴</span>
              </div>
            </div>
          </>
        )}

        {/* Status */}
        {status && (
          <div className={`status ${status.ok ? 'status-ok' : 'status-err'}`}>
            {status.text}
          </div>
        )}
      </div>

      {/* ── Sticky footer ── */}
      <div className="footer">
        <button
          className="submit-btn"
          onClick={submit}
          disabled={loading || cartCount === 0}
        >
          {loading
            ? '⏳ Відправляємо…'
            : cartCount === 0
              ? 'Оберіть товар'
              : `Замовити · ${total} ₴`}
        </button>
      </div>
    </>
  )
}
