import { useState, useEffect, useRef } from 'react';

export default function ChatBox({ caseId, user, onClose }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Connecting..."); // New Status State
  const ws = useRef(null);
  const endRef = useRef(null);

  useEffect(() => {
    // 1. Force 127.0.0.1 to avoid IPv6 issues
    const wsUrl = `ws://localhost:8000/ws/chat/${caseId}`;
    console.log("Attempting Connection to:", wsUrl);
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      console.log("✅ WebSocket Connected!");
      setStatus("Connected");
    };

    ws.current.onmessage = (event) => {
      console.log("📩 Message Received:", event.data);
      const msg = JSON.parse(event.data);
      setMsgs((prev) => {
        // Prevent duplicates if React renders twice
        if (prev.some(m => m.text === msg.text && m.user === msg.user && m.timestamp === msg.timestamp)) {
            return prev;
        }
        return [...prev, msg];
      });
    };

    ws.current.onclose = () => {
      console.log("❌ WebSocket Disconnected");
      setStatus("Disconnected");
    };

    ws.current.onerror = (error) => {
      console.error("⚠️ WebSocket Error:", error);
      setStatus("Error");
    };

    return () => {
      if(ws.current) ws.current.close();
    };
  }, [caseId]);

  // Auto-scroll to bottom
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const send = () => {
    if (!input || status !== "Connected") return;
    
    const payload = { 
      user, 
      text: input, 
      timestamp: new Date().toISOString() 
    };
    
    console.log("📤 Sending:", payload);
    ws.current.send(JSON.stringify(payload));
    setInput("");
  };

  return (
    <div className="chat-overlay">
      <div className="chat-window">
        {/* HEADER */}
        <div className="chat-header">
          <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
            <h3 style={{margin:0}}>💬 Case #{caseId}</h3>
            {/* STATUS DOT */}
            <span style={{
              height: '10px', width: '10px', borderRadius: '50%',
              backgroundColor: status === 'Connected' ? '#22c55e' : '#ef4444',
              display: 'inline-block', transition: 'background 0.3s'
            }} title={status}></span>
          </div>
          <button onClick={onClose} style={{background:'transparent', border:'none', color:'white', fontSize:'24px', cursor:'pointer'}}>×</button>
        </div>
        
        {/* BODY */}
        <div className="chat-body">
          {msgs.length === 0 && (
            <div style={{textAlign:'center', color:'#64748b', marginTop:'50px'}}>
              <p>No messages yet.</p>
              <p style={{fontSize:'12px'}}>Status: {status}</p>
            </div>
          )}
          
          {msgs.map((m, i) => (
            <div key={i} className={`chat-msg ${m.user === user ? 'mine' : 'theirs'}`}>
              <strong style={{fontSize:'10px', display:'block', marginBottom:'2px', opacity:0.7}}>{m.user}</strong>
              {m.text}
            </div>
          ))}
          <div ref={endRef} />
        </div>
        
        {/* FOOTER */}
        <div className="chat-footer">
          <input 
            value={input} 
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && send()}
            placeholder="Type message..." 
            autoFocus
            disabled={status !== 'Connected'}
          />
          <button onClick={send} disabled={status !== 'Connected'} style={{opacity: status !== 'Connected' ? 0.5 : 1}}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}