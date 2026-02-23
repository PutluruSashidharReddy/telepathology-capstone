import axios from 'axios';

export default function NetworkSim({ net, setNet }) {
  const changeNet = async (c) => {
    setNet(c);
    await axios.post(`${import.meta.env.VITE_API_URL}/network?condition=${c}`);
  };

  return (
    <div className="card">
      <h2 style={{color: '#c084fc'}}>🌍 Network Sim</h2>
      <div className="net-controls">
        {['Good', 'Poor', 'Critical'].map(c => (
          <button 
            key={c} 
            onClick={() => changeNet(c)} 
            className={`net-btn ${net === c ? 'active ' + c.toLowerCase() : ''}`}
          >
            {c}
          </button>
        ))}
      </div>
      <div style={{marginTop: '10px', fontSize: '12px', color: '#94a3b8'}}>
        Current Latency: {net === 'Good' ? '50ms' : net === 'Poor' ? '500ms' : 'High + Packet Loss'}
      </div>
    </div>
  );
}