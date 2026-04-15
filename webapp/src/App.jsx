import { useMemo, useState } from 'react'

const CATALOG = [
  { sku: 'hoodie_black', title: 'Худі Black', price: 1599 },
  { sku: 'cap_white', title: 'Кепка White', price: 799 },
  { sku: 'sticker_pack', title: 'Набір стікерів', price: 199 }
]

function validateForm(form) {
  if (form.name.trim().length < 2) return 'Вкажіть коректне ПІБ.'
  if (form.phone.trim().length < 5) return 'Вкажіть номер телефону.'
  if (form.cityName.trim().length < 2) return 'Вкажіть місто Нової Пошти.'
  if (form.warehouseName.trim().length < 2) return 'Вкажіть відділення/поштомат.'
  return null
}

export default function App() {
  const [cart, setCart] = useState({})
  const [form, setForm] = useState({
    name: '',
    phone: '',
    cityName: '',
    warehouseName: '',
    cityRef: '',
    warehouseRef: ''
  })
  const [status, setStatus] = useState('')
  const telegramStartParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param || null

  const items = useMemo(() => {
    return CATALOG.filter((item) => (cart[item.sku] || 0) > 0).map((item) => ({
      sku: item.sku,
      qty: cart[item.sku],
      price: item.price
    }))
  }, [cart])

  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.qty * item.price, 0),
    [items]
  )

  function updateQty(sku, qty) {
    setCart((prev) => ({ ...prev, [sku]: Math.max(0, qty) }))
  }

  function onSubmit(event) {
    event.preventDefault()

    const formError = validateForm(form)
    if (formError) {
      setStatus(formError)
      return
    }
    if (items.length === 0) {
      setStatus('Додайте хоча б один товар.')
      return
    }

    const deliveryInfo = `Нова Пошта: ${form.cityName.trim()}, ${form.warehouseName.trim()}`
    const payload = {
      customer: {
        name: form.name.trim(),
        phone: form.phone.trim(),
        delivery_info: deliveryInfo
      },
      items,
      meta: {
        source_code: telegramStartParam,
        webapp_version: 'v1',
        delivery_method: 'nova_poshta'
      },
      nova_poshta: {
        city_name: form.cityName.trim(),
        warehouse_name: form.warehouseName.trim(),
        city_ref: form.cityRef.trim() || null,
        warehouse_ref: form.warehouseRef.trim() || null
      }
    }

    const tg = window.Telegram?.WebApp
    if (!tg) {
      setStatus('Telegram WebApp SDK недоступний.')
      return
    }

    tg.sendData(JSON.stringify(payload))
    setStatus('Замовлення передано боту. Можна закрити сторінку.')
  }

  return (
    <main className="container">
      <h1>Магазин</h1>
      <section className="card">
        <h2>Каталог</h2>
        {CATALOG.map((item) => (
          <div key={item.sku} className="row">
            <div>
              <b>{item.title}</b>
              <span>{item.price} грн</span>
            </div>
            <input
              type="number"
              min="0"
              value={cart[item.sku] || 0}
              onChange={(e) => updateQty(item.sku, Number(e.target.value))}
            />
          </div>
        ))}
      </section>

      <section className="card">
        <h2>Оформлення</h2>
        <form onSubmit={onSubmit}>
          <label>
            ПІБ
            <input
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Іваненко Іван"
            />
          </label>
          <label>
            Телефон
            <input
              value={form.phone}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))}
              placeholder="+380..."
            />
          </label>
          <label>
            Місто (Нова Пошта)
            <input
              value={form.cityName}
              onChange={(e) => setForm((prev) => ({ ...prev, cityName: e.target.value }))}
              placeholder="Київ"
            />
          </label>
          <label>
            Відділення / Поштомат
            <input
              value={form.warehouseName}
              onChange={(e) => setForm((prev) => ({ ...prev, warehouseName: e.target.value }))}
              placeholder="Відділення №12"
            />
          </label>

          <details>
            <summary>Додатково (Ref для авто-ТТН)</summary>
            <label>
              City Ref
              <input
                value={form.cityRef}
                onChange={(e) => setForm((prev) => ({ ...prev, cityRef: e.target.value }))}
                placeholder="8d5a980d-..."
              />
            </label>
            <label>
              Warehouse Ref
              <input
                value={form.warehouseRef}
                onChange={(e) => setForm((prev) => ({ ...prev, warehouseRef: e.target.value }))}
                placeholder="841339c7-..."
              />
            </label>
          </details>

          <div className="summary">Сума: {total.toFixed(2)} грн</div>
          <button type="submit">Підтвердити замовлення</button>
        </form>
      </section>

      {status && <p className="status">{status}</p>}
    </main>
  )
}
