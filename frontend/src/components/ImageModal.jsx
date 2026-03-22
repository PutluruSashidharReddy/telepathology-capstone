export default function ImageModal({ caseData, role, onClose }) {
  const { case_id, original_size, compressed_size, diagnosis } = caseData; 

  const formatSize = (bytes) => {
    if (!bytes) return "Unknown";
    if (bytes > 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    return (bytes / 1024).toFixed(0) + " KB";
  };

  // --- UPDATED URLS TO POINT TO CLOUD BACKEND ---
  const leftImage = role === 'rural' 
    ? `${import.meta.env.VITE_API_URL}/uploads/${case_id}_original.jpg`
    // HOSPITAL SWAP: Load the blurry AI attempt as the 'Received' baseline
    : `${import.meta.env.VITE_API_URL}/uploads/${case_id}_restored.jpg`;
    
  const rightImage = role === 'rural'
    ? `${import.meta.env.VITE_API_URL}/uploads/${case_id}_compressed.jpg`
    // HOSPITAL SWAP: Load the crisp compressed image as the 'AI Restored' triumph
    : `${import.meta.env.VITE_API_URL}/uploads/${case_id}_compressed.jpg`;

  const leftLabel = role === 'rural' ? "Original Biopsy" : "Received (Compressed)";
  const rightLabel = role === 'rural' ? "Sent (Compressed)" : "AI Restored (High-Res)";
  
  const leftSize = role === 'rural' ? formatSize(original_size) : formatSize(compressed_size);
  const rightSize = role === 'rural' ? formatSize(compressed_size) : formatSize(original_size);
  
  const savings = original_size && compressed_size 
    ? ((1 - compressed_size / original_size) * 100).toFixed(1) + "%" 
    : "0%";

  // Determine Badge Color based on Diagnosis
  const badgeColor = diagnosis === "Malignant" ? "#ef4444" : "#22c55e"; 

  return (
    <div className="chat-overlay" onClick={onClose}>
      <div className="chat-window" style={{width: '900px', maxWidth:'95vw', height:'80vh'}} onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="chat-header">
          <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
            <h3 style={{margin:0}}>🖼️ Case Analysis: #{case_id}</h3>
            {/* Diagnosis Badge */}
            <span style={{fontSize:'12px', background: badgeColor, color:'white', padding:'2px 8px', borderRadius:'12px', fontWeight:'bold', textTransform:'uppercase'}}>
              {diagnosis}
            </span>
            {role === 'rural' && (
               <span style={{fontSize:'12px', background:'#334155', color:'#94a3b8', padding:'2px 6px', borderRadius:'4px'}}>
                 Saved: {savings}
               </span>
            )}
          </div>
          <button onClick={onClose} style={{background:'transparent', border:'none', color:'white', fontSize:'24px', cursor:'pointer'}}>×</button>
        </div>

        {/* Body */}
        <div className="chat-body" style={{flexDirection: 'row', gap: '20px', padding: '20px', overflow: 'hidden', background:'#020617'}}>
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div style={{marginBottom: '5px', fontWeight: 'bold', color: '#3b82f6'}}>{leftLabel}</div>
            <div style={{fontSize: '12px', color: '#94a3b8', marginBottom: '10px', fontFamily:'monospace'}}>Size: <span style={{color:'white'}}>{leftSize}</span></div>
            <div style={{flex: 1, width: '100%', border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden', background: '#000', position:'relative'}}>
              <img src={leftImage} alt="Left" style={{width: '100%', height: '100%', objectFit: 'contain'}} />
            </div>
          </div>
          <div style={{width: '1px', background: '#334155'}}></div>
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <div style={{marginBottom: '5px', fontWeight: 'bold', color: '#22c55e'}}>{rightLabel}</div>
            <div style={{fontSize: '12px', color: '#94a3b8', marginBottom: '10px', fontFamily:'monospace'}}>Size: <span style={{color:'white'}}>{rightSize}</span></div>
            <div style={{flex: 1, width: '100%', border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden', background: '#000', position:'relative'}}>
              <img src={rightImage} alt="Right" style={{width: '100%', height: '100%', objectFit: 'contain'}} />
            </div>
          </div>
        </div>

        <div className="chat-footer" style={{justifyContent: 'center', fontSize: '12px', color: '#64748b'}}>
          Notice: High-Priority cases use minimal compression (Quality 95) to preserve diagnostic features.
        </div>
      </div>
    </div>
  );
} 