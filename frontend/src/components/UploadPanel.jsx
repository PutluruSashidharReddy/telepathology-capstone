import { useState, useEffect } from 'react';
import axios from 'axios';

export default function UploadPanel() {
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState("");
  const [loading, setLoading] = useState(true);

  // 1. FETCH HOSPITALS FROM DB ON LOAD
  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/hospitals`);
        setHospitals(res.data);
        
        // Auto-select the first one if available
        if (res.data.length > 0) {
          setSelectedHospital(res.data[0]);
        }
      } catch (err) {
        console.error("Failed to load hospitals", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHospitals();
  }, []);

  const upload = async (e) => {
    if (!e.target.files.length) return;
    if (!selectedHospital) {
      alert("Please select a destination hospital first!");
      return;
    }

    const fd = new FormData();
    for (let i = 0; i < e.target.files.length; i++) {
      fd.append('files', e.target.files[i]);
    }

    const startTime = Date.now();
    const sender = localStorage.getItem('username') || 'Unknown Rural';

    // 3. SEND TO SELECTED HOSPITAL
    fd.append('sender', sender);
    fd.append('receiver', selectedHospital);

    try {
      await axios.post(`${import.meta.env.VITE_API_URL}/upload`, fd, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'X-Upload-Start': startTime.toString()
        }
      });
      alert(`Batch Upload Started! Sending to ${selectedHospital}.`);
    } catch (err) {
      alert("Upload Failed");
      console.error(err);
    }
  };

  return (
    <div className="card">
      <h2 className="text-blue">📡 Rural Uplink</h2>
      
      {/* DYNAMIC HOSPITAL DROPDOWN */}
      <div style={{marginBottom: '15px'}}>
        <label style={{display:'block', marginBottom:'5px', color:'#94a3b8', fontSize:'12px'}}>
          Select Destination Hospital:
        </label>
        
        {loading ? (
          <div style={{color:'#64748b', fontSize:'12px'}}>Loading active hospitals...</div>
        ) : hospitals.length === 0 ? (
          <div style={{color:'#ef4444', fontSize:'12px'}}>
            No Hospitals Found! (Register a user with role 'hospital')
          </div>
        ) : (
          <select 
            value={selectedHospital} 
            onChange={(e) => setSelectedHospital(e.target.value)}
            style={{
              width: '100%', padding: '10px', background: '#1e293b', 
              border: '1px solid #334155', color: 'white', borderRadius: '6px'
            }}
          >
            {hospitals.map(h => <option key={h} value={h}>{h}</option>)}
          </select>
        )}
      </div>

      <div className="upload-zone">
        <input 
          type="file" 
          onChange={upload} 
          className="upload-input" 
          multiple 
          disabled={hospitals.length === 0} // Disable if no destination
        />
        <p>Click to Upload Biopsy Slides</p>
        <small style={{color: '#64748b'}}>
          {selectedHospital ? `Routing to: ${selectedHospital}` : 'Waiting for selection...'}
        </small>
      </div>
    </div>
  );
}