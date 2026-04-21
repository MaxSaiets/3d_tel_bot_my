import { useRef, useState } from 'react'

function Placeholder({ title, accent }) {
  return (
    <div className="gallery-placeholder" style={{ '--product-accent': accent }}>
      <span className="gallery-placeholder-chip">Каталог</span>
      <strong>{title}</strong>
    </div>
  )
}

export default function Gallery({ images, title, accent }) {
  const [idx, setIdx] = useState(0)
  const startX = useRef(null)

  const safeImages = Array.isArray(images) ? images.filter(Boolean) : []
  if (!safeImages.length) {
    return <Placeholder title={title} accent={accent} />
  }

  const prev = () => setIdx((value) => (value - 1 + safeImages.length) % safeImages.length)
  const next = () => setIdx((value) => (value + 1) % safeImages.length)

  const onTouchStart = (event) => {
    startX.current = event.touches[0].clientX
  }

  const onTouchEnd = (event) => {
    if (startX.current === null) return
    const delta = event.changedTouches[0].clientX - startX.current
    if (delta > 50) prev()
    if (delta < -50) next()
    startX.current = null
  }

  return (
    <div className="gallery" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
      <div className="gallery-track" style={{ transform: `translateX(-${idx * 100}%)` }}>
        {safeImages.map((src, imageIndex) => (
          <div key={src} className="gallery-slide">
            <img src={src} alt={`${title} ${imageIndex + 1}`} loading={imageIndex === 0 ? 'eager' : 'lazy'} />
          </div>
        ))}
      </div>

      {safeImages.length > 1 && (
        <>
          <button className="gallery-arrow prev" onClick={prev} type="button" aria-label="Попереднє фото">
            ‹
          </button>
          <button className="gallery-arrow next" onClick={next} type="button" aria-label="Наступне фото">
            ›
          </button>
          <div className="gallery-dots">
            {safeImages.map((src, dotIndex) => (
              <button
                key={src}
                type="button"
                className={`gallery-dot${dotIndex === idx ? ' on' : ''}`}
                onClick={() => setIdx(dotIndex)}
                aria-label={`Фото ${dotIndex + 1}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
