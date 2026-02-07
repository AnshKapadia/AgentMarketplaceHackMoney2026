export default function Badge({ type, children }) {
  const cls = `d7-badge d7-badge-${type || 'available'}`
  return <span className={cls}>{children}</span>
}
