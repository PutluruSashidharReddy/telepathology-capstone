import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import UploadPanel from '../components/UploadPanel';
import SystemLogs from '../components/SystemLogs';
import TransferList from '../components/TransferList';
import ChatBox from '../components/ChatBox'; 
import ImageModal from '../components/ImageModal';

export default function Dashboard() {
  const [cases, setCases] = useState([]);
  const [logs, setLogs] = useState([]);
  
  const [activeChat, setActiveChat] = useState(null);
  const [activeCaseData, setActiveCaseData] = useState(null);
  
  const navigate = useNavigate();
  const role = localStorage.getItem('role') || 'rural';
  const username = localStorage.getItem('username') || 'User';

  const handleLogout = () => { localStorage.clear(); navigate('/'); };

  const handleSelectCase = (id) => {
    const selected = cases.find(c => c.case_id === id);
    if (selected) setActiveCaseData(selected);
  };

  useEffect(() => {
    const i = setInterval(async () => {
      try {
        // --- PASS USER INFO TO BOTH ENDPOINTS ---
        const c = await axios.get(`${import.meta.env.VITE_API_URL}/data?username=${username}&role=${role}`);
        const l = await axios.get(`${import.meta.env.VITE_API_URL}/logs?username=${username}&role=${role}`);
        
        setCases(c.data);
        setLogs(l.data);
      } catch (e) { 
        console.error("Backend Offline"); 
      }
    }, 800);
    return () => clearInterval(i);
  }, [username, role]);

  return (
    <div className="container">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'2rem'}}>
        <div>
          <h1 style={{margin:0}}>
            {role === 'rural' ? '🏡 Rural Dashboard' : '🏥 Hospital Command Center'}
          </h1>
          <div style={{color:'#94a3b8', display:'flex', alignItems:'center', gap:'10px'}}>
             <span>User: <strong>{username}</strong></span>
             <span style={{fontSize:'12px', background:'#334155', padding:'2px 6px', borderRadius:'4px'}}>{role.toUpperCase()}</span>
          </div>
        </div>
        <button onClick={handleLogout} style={{padding:'8px 16px', background:'#ef4444', color:'white', border:'none', borderRadius:'6px', cursor:'pointer', fontWeight:'bold'}}>Logout</button>
      </div>

      <div className="dashboard-grid">
        <div className="left-col">
          {/* Only Upload Panel (if rural) and Logs remain here */}
          {role === 'rural' && <UploadPanel />}
          <SystemLogs logs={logs} />
        </div>
        
        <TransferList 
          cases={cases} 
          role={role} 
          onChat={(id) => setActiveChat(id)} 
          onSelect={handleSelectCase} 
        />
      </div>

      {activeChat && <ChatBox caseId={activeChat} user={username} onClose={() => setActiveChat(null)} />}
      {activeCaseData && <ImageModal caseData={activeCaseData} role={role} onClose={() => setActiveCaseData(null)} />}
    </div>
  );
}