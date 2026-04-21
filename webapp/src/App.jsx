import { useEffect, useMemo, useState } from 'react'

import { FALLBACK_CATALOG } from './catalog'
import ChatWidget from './components/ChatWidget'
import Gallery from './components/Gallery'

const DELIVERY_TABS = [
  { id: 'nova_poshta', icon: '🚚', label: 'Нова Пошта' },
  { id: 'ukrposhta', icon: '📦', label: 'Укрпошта' },
  { id: 'pickup', icon: '🏪', label: 'Самовивіз' },
]
const DRAFT_STORAGE_KEY = 'telegram-shop-webapp-draft-v1'
const OFFER_VERSION = '2026-04-21'

function parseTgUser() {
  const tg = window.Telegram?.WebApp
  if (!tg) return null

  const parsedUser = tg.initDataUnsafe?.user
  if (parsedUser?.id) return parsedUser

  try {
    const raw = tg.initData || ''
    const params = new URLSearchParams(raw)
    const userStr = params.get('user')
    if (!userStr) return null
    const decoded = JSON.parse(decodeURIComponent(userStr))
    return decoded?.id ? decoded : null
  } catch {
    return null
  }
}

function money(value) {
  return new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 0 }).format(value)
}

function useDebounced(value, delayMs) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [delayMs, value])

  return debounced
}

function QuantityControl({ qty, onDecrease, onIncrease }) {
  return (
    <div className="qty">
      <button className="qty-btn" type="button" onClick={onDecrease} disabled={qty === 0} aria-label="Зменшити">
        −
      </button>
      <span className="qty-num">{qty}</span>
      <button className="qty-btn" type="button" onClick={onIncrease} aria-label="Збільшити">
        +
      </button>
    </div>
  )
}

function ProductCard({ product, qty, active, onSelect, onIncrease, onDecrease }) {
  const price = Number(product.price)
  const image = product.images?.[0]

  return (
    <article className={`product-card${active ? ' active' : ''}`} style={{ '--product-accent': product.accent }}>
      <button className="product-card-main" type="button" onClick={onSelect}>
        <div className="product-thumb">
          {image ? <img src={image} alt={product.title} loading="lazy" /> : <span>{product.short_title}</span>}
        </div>
        <div className="product-card-content">
          <div className="product-card-title-row">
            <h3>{product.short_title}</h3>
            {qty > 0 && <span className="product-chip">{qty} у кошику</span>}
          </div>
          <p>{product.subtitle}</p>
          <div className="product-card-price">
            {money(price)} грн <small>{product.unit_label}</small>
          </div>
        </div>
      </button>

      <div className="product-card-footer">
        <QuantityControl qty={qty} onDecrease={onDecrease} onIncrease={onIncrease} />
      </div>
    </article>
  )
}

function validateOrder({ cartItems, form, delivery, pickupRules }) {
  if (!cartItems.length) return '🛒 Додайте хоча б один товар у кошик.'
  if (form.name.trim().length < 2) return "Вкажіть ім'я та прізвище."
  if (!/^\+?[\d\s()\-]{7,}$/.test(form.phone.trim())) return 'Перевірте номер телефону.'

  if (delivery.method === 'nova_poshta') {
    if (!delivery.np.cityRef) return 'Оберіть місто для Нової Пошти.'
    if (!delivery.np.warehouseRef) return 'Оберіть відділення або поштомат Нової Пошти.'
  }

  if (delivery.method === 'ukrposhta') {
    if (!/^\d{5}$/.test(delivery.up.postcode.trim())) return 'Вкажіть коректний індекс Укрпошти.'
    if (delivery.up.city.trim().length < 2) return 'Вкажіть місто для доставки Укрпоштою.'
    if (delivery.up.postofficeName.trim().length < 3) return 'Вкажіть назву або номер відділення Укрпошти.'
    if (delivery.up.postofficeAddress.trim().length < 5) return 'Вкажіть адресу відділення Укрпошти.'
  }

  if (delivery.method === 'pickup') {
    const totalQty = cartItems.reduce((sum, item) => sum + item.qty, 0)
    if (totalQty < pickupRules.min_qty) {
      return `Самовивіз доступний від ${pickupRules.min_qty} штук.`
    }
  }

  return null
}

function loadDraft() {
  try {
    const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function buildDeliveryDetails(delivery, pickupRules) {
  if (delivery.method === 'nova_poshta') {
    return [
      { label: 'Спосіб', value: 'Нова Пошта' },
      { label: 'Місто', value: delivery.np.cityName || '—' },
      { label: 'Відділення / поштомат', value: delivery.np.warehouseName || '—' },
    ]
  }

  if (delivery.method === 'ukrposhta') {
    return [
      { label: 'Спосіб', value: 'Укрпошта' },
      { label: 'Індекс', value: delivery.up.postcode || '—' },
      { label: 'Місто', value: delivery.up.city || '—' },
      { label: 'Відділення', value: delivery.up.postofficeName || '—' },
      { label: 'Адреса відділення', value: delivery.up.postofficeAddress || '—' },
    ]
  }

  return [
    { label: 'Спосіб', value: 'Самовивіз' },
    { label: 'Місто', value: pickupRules.city },
    { label: 'Умова', value: `Від ${pickupRules.min_qty} штук` },
    { label: 'Примітка', value: pickupRules.note },
  ]
}

function OfferText() {
  return (
    <div className="offer-copy">
      <p>
        Нижче наведені загальні правила оформлення замовлення в цьому магазині. Вони описують, як обробляється
        замовлення, які дані передає покупець і що означає натискання кнопки підтвердження.
      </p>
      <div className="offer-points">
        <div>
          <strong>Формат продажу</strong>
          <span>Замовлення оформлюється дистанційно через Telegram WebApp.</span>
        </div>
        <div>
          <strong>Канал зв'язку</strong>
          <span>Уточнення та підтвердження виконуються через Telegram або за вказаним покупцем телефоном.</span>
        </div>
        <div>
          <strong>Підстава підтвердження</strong>
          <span>Покупець самостійно перевіряє склад замовлення, доставку та контакти перед відправкою заявки.</span>
        </div>
      </div>
      <ol className="offer-list">
        <li>Замовлення вважається прийнятим після підтвердження продавцем через Telegram, дзвінок або повідомлення.</li>
        <li>Ціна товару, склад замовлення, спосіб доставки та контактні дані фіксуються на екрані підтвердження перед відправкою.</li>
        <li>Оплата здійснюється у спосіб, зазначений під час оформлення замовлення. Для цього магазину базовий сценарій: оплата при отриманні, якщо інше не погоджено окремо.</li>
        <li>Доставка виконується службою, яку обрав покупець, за вказаними ним даними. Покупець відповідає за коректність індексу, міста, відділення та телефону отримувача.</li>
        <li>Самовивіз можливий лише на умовах, зазначених у магазині окремо.</li>
        <li>Повернення, обмін та розгляд звернень здійснюються відповідно до законодавства України та характеру товару. Якщо для конкретного товару діють окремі умови, вони мають бути додатково погоджені з покупцем у переписці.</li>
        <li>Натискання кнопки підтвердження означає акцепт цієї оферти та згоду покупця на обробку переданих ним даних для виконання замовлення.</li>
      </ol>
      <p className="offer-note">
        Орієнтир по правовій основі: Закон України <a href="https://zakon.rada.gov.ua/go/675-19" target="_blank" rel="noreferrer">«Про електронну комерцію»</a>, а також правила дистанційної торгівлі <a href="https://zakon.rada.gov.ua/go/z1181-07" target="_blank" rel="noreferrer">Наказ №103</a>. Це не замінює індивідуальну юридичну перевірку під твій бізнес.
      </p>
    </div>
  )
}

export default function App() {
  const tg = window.Telegram?.WebApp
  const tgUser = useMemo(() => parseTgUser(), [])

  const [catalog, setCatalog] = useState(FALLBACK_CATALOG)
  const [selectedSku, setSelectedSku] = useState(FALLBACK_CATALOG.items[0].sku)
  const [cart, setCart] = useState({})
  const [form, setForm] = useState({ name: '', phone: '' })
  const [delivery, setDelivery] = useState({
    method: 'nova_poshta',
    np: { cityQuery: '', cityName: '', cityRef: '', warehouseQuery: '', warehouseName: '', warehouseRef: '' },
    up: {
      postcode: '',
      officeQuery: '',
      city: '',
      postofficeId: '',
      postofficeName: '',
      postofficeAddress: '',
    },
    pickup: { city: FALLBACK_CATALOG.pickup_rules.city },
  })
  const [npCities, setNpCities] = useState([])
  const [npWarehouses, setNpWarehouses] = useState([])
  const [upOffices, setUpOffices] = useState([])
  const [npCityBusy, setNpCityBusy] = useState(false)
  const [npWarehouseBusy, setNpWarehouseBusy] = useState(false)
  const [upBusy, setUpBusy] = useState(false)
  const [upLookupEnabled, setUpLookupEnabled] = useState(true)
  const [upLookupMessage, setUpLookupMessage] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [offerAccepted, setOfferAccepted] = useState(false)
  const [offerExpanded, setOfferExpanded] = useState(false)

  const debouncedNpCity = useDebounced(delivery.np.cityQuery, 350)
  const debouncedNpWarehouse = useDebounced(delivery.np.warehouseQuery, 350)
  const debouncedUpQuery = useDebounced(delivery.up.officeQuery, 250)

  useEffect(() => {
    tg?.ready()
    tg?.expand()
  }, [tg])

  useEffect(() => {
    const draft = loadDraft()
    if (!draft) return

    if (draft.selectedSku) setSelectedSku(draft.selectedSku)
    if (draft.cart && typeof draft.cart === 'object') setCart(draft.cart)
    if (draft.form && typeof draft.form === 'object') {
      setForm((prev) => ({ ...prev, ...draft.form }))
    }
    if (typeof draft.offerAccepted === 'boolean') {
      setOfferAccepted(draft.offerAccepted)
    }
    if (draft.delivery && typeof draft.delivery === 'object') {
      setDelivery((prev) => ({
        ...prev,
        ...draft.delivery,
        np: { ...prev.np, ...(draft.delivery.np || {}) },
        up: { ...prev.up, ...(draft.delivery.up || {}) },
        pickup: { ...prev.pickup, ...(draft.delivery.pickup || {}) },
      }))
    }
  }, [])

  useEffect(() => {
    fetch('/api/catalog')
      .then((response) => (response.ok ? response.json() : FALLBACK_CATALOG))
      .then((data) => {
        if (!data?.items?.length) return
        setCatalog(data)
        setSelectedSku((current) => (data.items.some((item) => item.sku === current) ? current : data.items[0].sku))
        setDelivery((prev) => ({
          ...prev,
          pickup: { city: data.pickup_rules?.city || FALLBACK_CATALOG.pickup_rules.city },
        }))
      })
      .catch(() => {})
  }, [])

  const currentProduct = catalog.items.find((item) => item.sku === selectedSku) || catalog.items[0]
  const cartItems = catalog.items
    .map((product) => ({ ...product, qty: cart[product.sku] || 0 }))
    .filter((product) => product.qty > 0)
  const totalQty = cartItems.reduce((sum, item) => sum + item.qty, 0)
  const totalAmount = cartItems.reduce((sum, item) => sum + item.qty * Number(item.price), 0)
  const deliveryDetails = buildDeliveryDetails(delivery, catalog.pickup_rules)

  useEffect(() => {
    if (delivery.method !== 'nova_poshta') return
    if (delivery.np.cityRef || debouncedNpCity.trim().length < 2) {
      setNpCities([])
      return
    }

    let alive = true
    setNpCityBusy(true)
    fetch(`/api/np/cities?query=${encodeURIComponent(debouncedNpCity.trim())}`)
      .then((response) => (response.ok ? response.json() : { items: [] }))
      .then((data) => {
        if (!alive) return
        setNpCities((data.items || []).slice(0, 8))
      })
      .catch(() => {
        if (alive) setNpCities([])
      })
      .finally(() => {
        if (alive) setNpCityBusy(false)
      })

    return () => {
      alive = false
    }
  }, [debouncedNpCity, delivery.method, delivery.np.cityRef])

  useEffect(() => {
    if (delivery.method !== 'nova_poshta' || !delivery.np.cityRef) {
      setNpWarehouses([])
      return
    }

    let alive = true
    setNpWarehouseBusy(true)
    const query = debouncedNpWarehouse.trim()
    const querySuffix = query ? `&query=${encodeURIComponent(query)}` : ''
    fetch(`/api/np/warehouses?city_ref=${encodeURIComponent(delivery.np.cityRef)}${querySuffix}`)
      .then((response) => (response.ok ? response.json() : { items: [] }))
      .then((data) => {
        if (!alive) return
        setNpWarehouses((data.items || []).slice(0, 12))
      })
      .catch(() => {
        if (alive) setNpWarehouses([])
      })
      .finally(() => {
        if (alive) setNpWarehouseBusy(false)
      })

    return () => {
      alive = false
    }
  }, [debouncedNpWarehouse, delivery.method, delivery.np.cityRef])

  useEffect(() => {
    if (delivery.method !== 'ukrposhta') return
    if (!/^\d{5}$/.test(delivery.up.postcode.trim())) {
      setUpOffices([])
      setUpLookupMessage('')
      return
    }

    let alive = true
    setUpBusy(true)
    setUpLookupEnabled(true)
    const query = debouncedUpQuery.trim()
    const querySuffix = query ? `&query=${encodeURIComponent(query)}` : ''
    fetch(`/api/up/postoffices?postcode=${delivery.up.postcode.trim()}${querySuffix}`)
      .then(async (response) => {
        if (response.ok) return response.json()
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Не вдалося отримати список відділень Укрпошти.')
      })
      .then((data) => {
        if (!alive) return
        setUpOffices((data.items || []).slice(0, 20))
        setUpLookupMessage((data.items || []).length ? '' : 'За цим індексом можна заповнити відділення вручну.')
      })
      .catch((error) => {
        if (!alive) return
        setUpOffices([])
        setUpLookupEnabled(false)
        setUpLookupMessage(`${error.message} Можна ввести відділення вручну.`)
      })
      .finally(() => {
        if (alive) setUpBusy(false)
      })

    return () => {
      alive = false
    }
  }, [debouncedUpQuery, delivery.method, delivery.up.postcode])

  useEffect(() => {
    try {
      window.localStorage.setItem(
        DRAFT_STORAGE_KEY,
        JSON.stringify({
          selectedSku,
          cart,
          form,
          delivery,
          offerAccepted,
        })
      )
    } catch {
      // Ignore storage failures in limited webviews.
    }
  }, [selectedSku, cart, form, delivery, offerAccepted])

  function changeQty(sku, delta) {
    setCart((prev) => {
      const nextQty = Math.max(0, (prev[sku] || 0) + delta)
      if (!nextQty) {
        const next = { ...prev }
        delete next[sku]
        return next
      }
      return { ...prev, [sku]: nextQty }
    })
  }

  function pickNpCity(city) {
    const cityName = city.Present || city.MainDescription || ''
    const cityRef = city.DeliveryCity || city.Ref || ''
    setDelivery((prev) => ({
      ...prev,
      np: {
        cityQuery: cityName,
        cityName,
        cityRef,
        warehouseQuery: '',
        warehouseName: '',
        warehouseRef: '',
      },
    }))
    setNpCities([])
  }

  function pickNpWarehouse(warehouse) {
    const warehouseName = warehouse.Description || warehouse.ShortAddress || ''
    const warehouseRef = warehouse.Ref || ''
    setDelivery((prev) => ({
      ...prev,
      np: { ...prev.np, warehouseQuery: warehouseName, warehouseName, warehouseRef },
    }))
    setNpWarehouses([])
  }

  function pickUpOffice(office) {
    setDelivery((prev) => ({
      ...prev,
      up: {
        ...prev.up,
        city: office.city,
        postofficeId: office.id,
        postofficeName: office.name,
        postofficeAddress: office.address,
        officeQuery: `${office.name}${office.address ? `, ${office.address}` : ''}`,
      },
    }))
    setUpLookupMessage('Відділення обрано зі списку.')
  }

  function buildDeliveryInfo() {
    if (delivery.method === 'nova_poshta') {
      return `Нова Пошта: ${delivery.np.cityName}, ${delivery.np.warehouseName}`
    }
    if (delivery.method === 'ukrposhta') {
      return `Укрпошта: ${delivery.up.postcode}, ${delivery.up.city}, ${delivery.up.postofficeName}`
    }
    return `${catalog.pickup_rules.note}`
  }

  function handleCheckout() {
    const error = validateOrder({ cartItems, form, delivery, pickupRules: catalog.pickup_rules })
    if (error) {
      setStatus({ ok: false, text: error })
      return
    }
    if (!offerAccepted) {
      setStatus({ ok: false, text: 'Підтвердіть ознайомлення з умовами оферти перед оформленням замовлення.' })
      return
    }
    if (!tgUser?.id) {
      setStatus({
        ok: false,
        text: '⚠️ Не вдалося визначити Telegram ID. Закрийте магазин і відкрийте його з бота ще раз.',
      })
      return
    }
    setStatus(null)
    setShowConfirm(true)
  }

  async function submitOrder() {
    setLoading(true)
    setShowConfirm(false)
    setStatus(null)

    const payload = {
      customer: {
        name: form.name.trim(),
        phone: form.phone.trim(),
        delivery_info: buildDeliveryInfo(),
      },
      items: cartItems.map((item) => ({ sku: item.sku, qty: item.qty, price: Number(item.price) })),
      meta: {
        source_code: tg?.initDataUnsafe?.start_param || null,
        webapp_version: 'v5',
        delivery_method: delivery.method,
      },
      nova_poshta:
        delivery.method === 'nova_poshta'
          ? {
              city_name: delivery.np.cityName,
              warehouse_name: delivery.np.warehouseName,
              city_ref: delivery.np.cityRef || null,
              warehouse_ref: delivery.np.warehouseRef || null,
            }
          : null,
      ukr_poshta:
        delivery.method === 'ukrposhta'
          ? {
              postcode: delivery.up.postcode.trim(),
              city: delivery.up.city,
              postoffice_id: delivery.up.postofficeId,
              postoffice_name: delivery.up.postofficeName,
              postoffice_address: delivery.up.postofficeAddress,
            }
          : null,
      pickup:
        delivery.method === 'pickup'
          ? {
              city: catalog.pickup_rules.city,
              note: catalog.pickup_rules.note,
            }
          : null,
      telegram_user_id: tgUser.id,
      telegram_username: tgUser.username || null,
    }

    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        setStatus({ ok: false, text: `Помилка: ${error.detail || response.status}` })
        return
      }

      const data = await response.json()
      setStatus({
        ok: true,
        text: `✅ Замовлення #${data.order_uuid.slice(0, 8)} прийнято. Очікуйте повідомлення від бота.`,
      })
      try {
        window.localStorage.removeItem(DRAFT_STORAGE_KEY)
      } catch {
        // Ignore storage cleanup failures.
      }
      setCart({})
      setOfferAccepted(false)
      setDelivery((prev) => ({
        ...prev,
        np: { cityQuery: '', cityName: '', cityRef: '', warehouseQuery: '', warehouseName: '', warehouseRef: '' },
        up: { postcode: '', officeQuery: '', city: '', postofficeId: '', postofficeName: '', postofficeAddress: '' },
      }))
      window.setTimeout(() => tg?.close(), 2600)
    } catch (error) {
      setStatus({ ok: false, text: `Мережева помилка: ${error.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="page-shell">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">Telegram Shop</span>
            <h1>Каталог із кількома товарами, швидким оформленням та чатом підтримки</h1>
            <p>
              Додавайте товари в один кошик, обирайте доставку, а для самовивозу одразу бачите правила:
              лише Хмельницький, від {catalog.pickup_rules.min_qty} штук, за домовленістю.
            </p>
          </div>
          <div className="hero-rules">
            <div className="rule-card">
              <strong>Оплата</strong>
              <span>Після отримання товару</span>
            </div>
            <div className="rule-card">
              <strong>Доставка</strong>
              <span>Нова Пошта, Укрпошта або самовивіз</span>
            </div>
            <div className="rule-card">
              <strong>Самовивіз</strong>
              <span>{catalog.pickup_rules.note}</span>
            </div>
          </div>
        </section>

        <section className="catalog-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Каталог</span>
              <h2>Оберіть товари</h2>
            </div>
            <div className="summary-pill">
              {totalQty ? `У кошику ${totalQty} шт. на ${money(totalAmount)} грн` : 'Кошик поки порожній'}
            </div>
          </div>

          {(totalQty > 0 || form.name || form.phone) && (
            <div className="draft-pill">Чернетка кошика і доставки зберігається автоматично між відкриттями магазину</div>
          )}

          <div className="product-grid">
            {catalog.items.map((product) => (
              <ProductCard
                key={product.sku}
                product={product}
                qty={cart[product.sku] || 0}
                active={currentProduct.sku === product.sku}
                onSelect={() => setSelectedSku(product.sku)}
                onIncrease={() => changeQty(product.sku, 1)}
                onDecrease={() => changeQty(product.sku, -1)}
              />
            ))}
          </div>
        </section>

        <section className="product-spotlight">
          <div className="spotlight-media">
            <Gallery images={currentProduct.images} title={currentProduct.title} accent={currentProduct.accent} />
          </div>
          <div className="spotlight-copy">
            <div className="spotlight-badges">
              {currentProduct.badges.map((badge) => (
                <span key={badge} className="badge">
                  {badge}
                </span>
              ))}
            </div>
            <h2>{currentProduct.title}</h2>
            <div className="spotlight-price">
              {money(Number(currentProduct.price))} грн <small>{currentProduct.unit_label}</small>
            </div>
            <p className="spotlight-description">{currentProduct.description}</p>
            <div className="feature-list">
              {currentProduct.features.map((feature) => (
                <div key={feature} className="feature-item">
                  <span>•</span>
                  <span>{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="checkout-layout">
          <div className="checkout-main">
            <div className="panel">
              <div className="panel-heading">
                <span className="eyebrow">Доставка</span>
                <h2>Оберіть зручний спосіб отримання</h2>
              </div>

              <div className="delivery-tabs">
                {DELIVERY_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`delivery-tab${delivery.method === tab.id ? ' active' : ''}`}
                    onClick={() => setDelivery((prev) => ({ ...prev, method: tab.id }))}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              {delivery.method === 'nova_poshta' && (
                <div className="form-grid">
                  <label className="field">
                    <span>Місто</span>
                    <input
                      value={delivery.np.cityQuery}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          np: {
                            ...prev.np,
                            cityQuery: event.target.value,
                            cityName: '',
                            cityRef: '',
                            warehouseQuery: '',
                            warehouseName: '',
                            warehouseRef: '',
                          },
                        }))
                      }
                      placeholder="Почніть вводити місто"
                    />
                    {npCityBusy && <small>Шукаємо міста…</small>}
                    {!!npCities.length && (
                      <div className="dropdown-list">
                        {npCities.map((city, index) => (
                          <button key={`${city.Ref || city.DeliveryCity}-${index}`} type="button" onClick={() => pickNpCity(city)}>
                            <strong>{city.MainDescription || city.Present}</strong>
                            <span>{city.AreaDescription ? `${city.AreaDescription} обл.` : 'Місто'}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </label>

                  <label className="field">
                    <span>Відділення або поштомат</span>
                    <input
                      value={delivery.np.warehouseQuery}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          np: {
                            ...prev.np,
                            warehouseQuery: event.target.value,
                            warehouseName: '',
                            warehouseRef: '',
                          },
                        }))
                      }
                      placeholder={delivery.np.cityRef ? 'Введіть назву відділення' : 'Спершу оберіть місто'}
                      disabled={!delivery.np.cityRef}
                    />
                    {npWarehouseBusy && <small>Завантажуємо відділення…</small>}
                    {!!npWarehouses.length && (
                      <div className="dropdown-list">
                        {npWarehouses.map((warehouse, index) => (
                          <button key={`${warehouse.Ref}-${index}`} type="button" onClick={() => pickNpWarehouse(warehouse)}>
                            <strong>{warehouse.Description}</strong>
                          </button>
                        ))}
                      </div>
                    )}
                  </label>
                </div>
              )}

              {delivery.method === 'ukrposhta' && (
                <div className="form-grid">
                  <label className="field">
                    <span>Поштовий індекс</span>
                    <input
                      value={delivery.up.postcode}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          up: {
                            ...prev.up,
                            postcode: event.target.value.replace(/\D/g, '').slice(0, 5),
                            officeQuery: '',
                            city: '',
                            postofficeId: '',
                            postofficeName: '',
                            postofficeAddress: '',
                          },
                        }))
                      }
                      placeholder="Наприклад: 29000"
                      inputMode="numeric"
                    />
                    <small>Вкажіть 5 цифр індексу. За ним спробуємо знайти доступні відділення.</small>
                  </label>

                  <label className="field">
                    <span>Місто</span>
                    <input
                      value={delivery.up.city}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          up: {
                            ...prev.up,
                            city: event.target.value,
                          },
                        }))
                      }
                      placeholder="Наприклад: Хмельницький"
                    />
                    <small>Напишіть місто саме так, як воно має бути в даних для відправки.</small>
                  </label>

                  <label className="field">
                    <span>Пошук відділення Укрпошти</span>
                    <input
                      value={delivery.up.officeQuery}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          up: {
                            ...prev.up,
                            officeQuery: event.target.value,
                            postofficeId: '',
                            postofficeName: '',
                            postofficeAddress: '',
                          },
                        }))
                      }
                      placeholder={/^\d{5}$/.test(delivery.up.postcode) ? 'Спробуйте знайти відділення' : 'Спершу вкажіть індекс'}
                      disabled={!/^\d{5}$/.test(delivery.up.postcode)}
                    />
                    {upBusy && <small>Шукаємо відділення…</small>}
                    {!!upOffices.length && (
                      <div className="dropdown-list">
                        {upOffices.map((office) => (
                          <button key={office.id} type="button" onClick={() => pickUpOffice(office)}>
                            <strong>{office.name}</strong>
                            <span>
                              {office.city}
                              {office.address ? `, ${office.address}` : ''}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </label>

                  <label className="field">
                    <span>Назва або номер відділення</span>
                    <input
                      value={delivery.up.postofficeName}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          up: {
                            ...prev.up,
                            postofficeId: '',
                            postofficeName: event.target.value,
                          },
                        }))
                      }
                      placeholder="Наприклад: Відділення №1"
                    />
                    <small>Якщо не знайшли у списку, впишіть вручну номер або назву відділення.</small>
                  </label>

                  <label className="field">
                    <span>Адреса відділення</span>
                    <input
                      value={delivery.up.postofficeAddress}
                      onChange={(event) =>
                        setDelivery((prev) => ({
                          ...prev,
                          up: {
                            ...prev.up,
                            postofficeId: '',
                            postofficeAddress: event.target.value,
                          },
                        }))
                      }
                      placeholder="Наприклад: вул. Проскурівська, 1"
                    />
                    <small>Адреса допомагає перевірити, що обране саме те відділення.</small>
                  </label>

                  {upLookupMessage && (
                    <div className={`delivery-note ${upLookupEnabled ? 'success' : 'warning'}`}>{upLookupMessage}</div>
                  )}
                </div>
              )}

              {delivery.method === 'pickup' && (
                <div className="delivery-note warning">
                  🏪 Самовивіз доступний лише по місту {catalog.pickup_rules.city}, від {catalog.pickup_rules.min_qty}{' '}
                  штук і тільки за попередньою домовленістю. Якщо хочете самовивіз на меншу кількість, напишіть нам у
                  чат підтримки.
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-heading">
                <span className="eyebrow">Контакти</span>
                <h2>Ваші дані для підтвердження</h2>
              </div>

              <div className="form-grid">
                <label className="field">
                  <span>Ім'я та прізвище</span>
                  <input
                    value={form.name}
                    onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                    placeholder="Іваненко Іван Іванович"
                  />
                </label>

                <label className="field">
                  <span>Телефон</span>
                  <input
                    value={form.phone}
                    onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
                    placeholder="+38 (0__) ___-__-__"
                    inputMode="tel"
                  />
                </label>
              </div>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <span className="eyebrow">Оферта</span>
                <h2>Умови оформлення замовлення</h2>
              </div>

              <div className="offer-card">
                <div className="offer-summary">
                  <div>
                    <strong>Публічна оферта та обробка даних</strong>
                    <span>Версія шаблону: {OFFER_VERSION}</span>
                  </div>
                  <button type="button" className="secondary-btn compact-btn" onClick={() => setOfferExpanded((value) => !value)}>
                    {offerExpanded ? 'Сховати умови' : 'Переглянути умови'}
                  </button>
                </div>

                {offerExpanded && <OfferText />}

                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={offerAccepted}
                    onChange={(event) => setOfferAccepted(event.target.checked)}
                  />
                  <span>
                    Я ознайомився(-лась) з умовами оферти, погоджуюсь із деталями замовлення та надаю дані для
                    виконання доставки.
                  </span>
                </label>
              </div>
            </div>
          </div>

          <aside className="checkout-side">
            <div className="panel sticky-panel">
              <div className="panel-heading">
                <span className="eyebrow">Кошик</span>
                <h2>Ваше замовлення</h2>
              </div>

              {!cartItems.length && <div className="empty-cart">Додайте товари з каталогу, щоб побачити підсумок.</div>}

              {cartItems.map((item) => (
                <div key={item.sku} className="summary-row">
                  <div>
                    <strong>{item.short_title}</strong>
                    <span>{item.qty} шт.</span>
                  </div>
                  <strong>{money(item.qty * Number(item.price))} грн</strong>
                </div>
              ))}

              <div className="summary-total">
                <span>Разом</span>
                <strong>{money(totalAmount)} грн</strong>
              </div>

              <div className="summary-meta">
                <div>Оплата після отримання</div>
                <div>{buildDeliveryInfo()}</div>
                <div>{offerAccepted ? 'Оферту підтверджено' : 'Потрібно підтвердити оферту'}</div>
              </div>

              {status && <div className={`status ${status.ok ? 'success' : 'error'}`}>{status.text}</div>}

              <button className="submit-btn" type="button" onClick={handleCheckout} disabled={loading || !cartItems.length}>
                {loading ? '⏳ Відправляємо…' : `Оформити замовлення • ${money(totalAmount)} грн`}
              </button>
            </div>
          </aside>
        </section>
      </div>

      <ChatWidget tgUserId={tgUser?.id} />

      {showConfirm && (
        <div className="confirm-overlay" onClick={(event) => event.target === event.currentTarget && setShowConfirm(false)}>
          <div className="confirm-panel">
            <div className="confirm-header">
              <div>
                <span className="eyebrow">Підтвердження</span>
                <h2>Перевірте замовлення</h2>
              </div>
              <button className="chat-close" type="button" onClick={() => setShowConfirm(false)} aria-label="Закрити">
                ✕
              </button>
            </div>

            <div className="confirm-body">
              <div className="confirm-block">
                <strong>Що ви замовляєте</strong>
                <p>Перевірте весь склад замовлення, кількість, доставку та контактні дані перед відправкою.</p>
              </div>

              {cartItems.map((item) => (
                <div key={item.sku} className="summary-row detailed-row">
                  <div>
                    <strong>{item.short_title}</strong>
                    <span>{item.qty} шт. × {money(Number(item.price))} грн</span>
                  </div>
                  <strong>{money(item.qty * Number(item.price))} грн</strong>
                </div>
              ))}

              <div className="confirm-block">
                <strong>Доставка</strong>
                <div className="detail-list">
                  {deliveryDetails.map((detail) => (
                    <div key={detail.label} className="detail-row">
                      <span>{detail.label}</span>
                      <strong>{detail.value}</strong>
                    </div>
                  ))}
                </div>
              </div>

              <div className="confirm-block">
                <strong>Контакти</strong>
                <div className="detail-list">
                  <div className="detail-row">
                    <span>Отримувач</span>
                    <strong>{form.name}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Телефон</span>
                    <strong>{form.phone}</strong>
                  </div>
                </div>
              </div>

              <div className="confirm-block">
                <strong>Оферта</strong>
                <div className="detail-list">
                  <div className="detail-row">
                    <span>Статус</span>
                    <strong>{offerAccepted ? 'Підтверджено' : 'Не підтверджено'}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Версія шаблону</span>
                    <strong>{OFFER_VERSION}</strong>
                  </div>
                </div>
              </div>

              <div className="summary-total">
                <span>До сплати</span>
                <strong>{money(totalAmount)} грн</strong>
              </div>
            </div>

            <div className="confirm-actions">
              <button className="secondary-btn" type="button" onClick={() => setShowConfirm(false)}>
                Редагувати
              </button>
              <button className="submit-btn" type="button" onClick={submitOrder} disabled={loading}>
                Підтвердити замовлення
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
