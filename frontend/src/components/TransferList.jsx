export default function TransferList({ cases, role, onChat, onSelect }) {
  return (
    <div className="right-col">
      <h2 style={{marginTop: 0}}>
        {role === 'rural' ? '🚀 Active Transfers' : '📥 Incoming Priority Queue'}
      </h2>

      {cases.length === 0 && (
        <div style={{padding: '2rem', textAlign: 'center', border: '1px dashed #334155', borderRadius: '8px', color: '#64748b'}}>
          No active cases found.
        </div>
      )}

      {cases.map(c => {
        const isPaused = c.transfer?.status.includes('Paused');
        const isHigh = c.priority === 'High';
        const isComplete = c.transfer?.status.includes('Completed');
        const statusColor = isPaused ? 'text-yellow' : isHigh ? 'text-red' : 'text-blue';
        const barClass = isPaused ? 'fill-yellow' : isHigh ? 'fill-red' : 'fill-blue';

        // --- NEW ROUTING BADGE LOGIC ---
        const routeLabel = role === 'rural' ? `To: ${c.receiver}` : `From: ${c.sender}`;

        return (
          <div 
            key={c.case_id} 
            className={`transfer-card ${c.priority}`} 
            style={{position:'relative', cursor: 'pointer', transition: 'transform 0.2s'}}
            onClick={() => onSelect(c.case_id)}
            onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.02)"}
            onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
          >
            <div className="transfer-header">
              <div className="transfer-info">
                <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                  <h3 style={{margin:0}}>Case #{c.case_id}</h3>
                  <span className={`badge ${c.diagnosis === 'Malignant' ? 'bg-red' : 'bg-green'}`}>{c.diagnosis}</span>
                  <button onClick={(e) => { e.stopPropagation(); onChat(c.case_id); }} className="chat-btn">💬 Chat</button>
                </div>
                
                {/* --- DISPLAY ROUTING INFO --- */}
                <div style={{fontSize: '11px', color: '#cbd5e1', marginTop: '4px', display:'flex', gap:'10px'}}>
                  <span>Priority: <span className={isHigh ? 'text-red font-bold' : 'text-blue'}>{c.priority}</span></span>
                  <span style={{background:'rgba(255,255,255,0.1)', padding:'0 4px', borderRadius:'3px'}}>{routeLabel}</span>
                </div>
              </div>

              {!isComplete && (
                <div className="speed-display">
                  <div className="speed-val">{c.transfer?.speed || "0 KB/s"}</div>
                  <div className={`status-val ${statusColor} ${isPaused ? 'animate-pulse' : ''}`}>{c.transfer?.status}</div>
                </div>
              )}
            </div>

            <div className="progress-track">
              <div className={`progress-fill ${barClass}`} style={{ width: `${c.transfer?.progress}%` }}></div>
            </div>

            <div style={{marginTop: '12px'}}>
              {isComplete ? (
                 <div style={{display: 'grid', gridTemplateColumns: '1fr', gap: '10px', background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155'}}>
                   <div style={{textAlign: 'center'}}>
                     <div style={{fontSize: '10px', color: '#94a3b8'}}>AVG SPEED</div>
                     <div style={{color: '#3b82f6', fontWeight: 'bold', fontSize: '13px'}}>{c.transfer?.stats?.avg}</div>
                   </div>
                 </div>
              ) : (
                 <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', fontFamily: 'monospace'}}>
                   <span>Chunk: {c.transfer?.current_chunk} / {c.transfer?.total_chunks}</span>
                   <span>{c.transfer?.progress}% Complete</span>
                 </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}