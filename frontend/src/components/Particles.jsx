export default function Particles({ count = 7 }) {
  return [...Array(count)].map((_, i) => (
    <div key={i} className="d7-particle" style={{
      left: `${10 + i * 13}%`,
      top: `${15 + (i % 4) * 22}%`,
      animationDelay: `${i * 1.1}s`,
      animationDuration: `${7 + i * 1.2}s`,
    }} />
  ))
}
