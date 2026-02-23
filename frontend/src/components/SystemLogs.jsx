export default function SystemLogs({ logs }) {
  return (
    <div className="logs-panel">
      <div style={{position: 'sticky', top: 0, background: '#0b1120', paddingBottom: '5px', fontWeight: 'bold', color: '#475569'}}>
        SYSTEM KERNEL LOGS
      </div>
      {logs.map((l, i) => (
        <div key={i} className="log-item" style={{ color: l.type === 'error' ? '#ef4444' : l.type === 'warning' ? '#eab308' : '#22c55e' }}>
          <span className="log-time">[{l.timestamp.substring(11, 19)}]</span>
          {l.message}
        </div>
      ))}
    </div>
  );
}