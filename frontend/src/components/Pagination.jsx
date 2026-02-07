export default function Pagination({ page, total, limit, onPage }) {
  const pages = Math.ceil(total / limit)
  if (pages <= 1) return null
  return (
    <div className="d7-pagination">
      <button disabled={page <= 1} onClick={() => onPage(page - 1)}>&laquo;</button>
      {[...Array(Math.min(pages, 7))].map((_, i) => {
        const p = i + 1
        return <button key={p} className={p === page ? 'active' : ''} onClick={() => onPage(p)}>{p}</button>
      })}
      <button disabled={page >= pages} onClick={() => onPage(page + 1)}>&raquo;</button>
    </div>
  )
}
