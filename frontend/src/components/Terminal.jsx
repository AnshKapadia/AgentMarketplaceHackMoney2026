export default function Terminal({ title = 'agenthive-cli', lines = [], animate = true }) {
  return (
    <div className="d7-terminal">
      <div className="d7-terminal-bar">
        <div className="d7-terminal-dot" />
        <div className="d7-terminal-dot" />
        <div className="d7-terminal-dot" />
        <div className="d7-terminal-title">{title}</div>
      </div>
      <div className="d7-terminal-body">
        {lines.map((line, i) => (
          <div key={i} className={animate ? 'd7-terminal-line' : ''} style={animate ? { animationDelay: `${i * 0.5}s` } : {}}>
            {line.prompt && <span className="d7-t-prompt">{line.prompt}</span>}
            {line.cmd && <span className="d7-t-cmd">{line.cmd}</span>}
            {line.out && <span className="d7-t-out">{line.out}</span>}
            {line.ok && <span className="d7-t-ok">{line.ok}</span>}
            {line.badge && <span className="d7-t-badge">{line.badge}</span>}
          </div>
        ))}
      </div>
    </div>
  )
}
