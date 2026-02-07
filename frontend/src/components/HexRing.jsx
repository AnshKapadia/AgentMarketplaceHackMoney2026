export default function HexRing({ label = 'AGNT', sub = 'Native Token' }) {
  return (
    <div className="d7-hex-ring">
      <svg viewBox="0 0 350 350" fill="none">
        <polygon points="175,15 325,95 325,255 175,335 25,255 25,95" stroke="#f0a500" strokeWidth="0.5" fill="none" opacity="0.3" />
        <polygon points="175,45 295,110 295,240 175,305 55,240 55,110" stroke="#f0a500" strokeWidth="0.5" fill="none" opacity="0.2" />
        <polygon points="175,75 265,125 265,225 175,275 85,225 85,125" stroke="#f0a500" strokeWidth="0.5" fill="none" opacity="0.15" />
        <circle cx="175" cy="15" r="3" fill="#f0a500" opacity="0.6" />
        <circle cx="325" cy="95" r="3" fill="#f0a500" opacity="0.6" />
        <circle cx="325" cy="255" r="3" fill="#f0a500" opacity="0.6" />
        <circle cx="175" cy="335" r="3" fill="#f0a500" opacity="0.6" />
        <circle cx="25" cy="255" r="3" fill="#f0a500" opacity="0.6" />
        <circle cx="25" cy="95" r="3" fill="#f0a500" opacity="0.6" />
      </svg>
      <div className="d7-hex-center">
        <div className="d7-hex-label">{label}</div>
        <div className="d7-hex-sub">{sub}</div>
      </div>
    </div>
  )
}
