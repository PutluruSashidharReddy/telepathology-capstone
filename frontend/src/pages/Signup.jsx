import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Signup() {
  const [formData, setFormData] = useState({ username: '', password: '', role: 'rural' });
  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      await axios.post(`${import.meta.env.VITE_API_URL}/auth/signup`, formData);
      alert("Account Created! Please Login.");
      navigate('/');
    } catch (e) {
      alert("Signup Failed: Username might exist.");
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="text-blue text-center">Create Account</h1>
        <p className="text-center" style={{color:'#94a3b8', marginBottom:'20px'}}>Join Telepathology Network</p>
        
        <input className="login-input" placeholder="Username" onChange={e => setFormData({...formData, username: e.target.value})} />
        <input className="login-input" type="password" placeholder="Password" onChange={e => setFormData({...formData, password: e.target.value})} />
        
        <select className="login-select" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
          <option value="rural">Rural Clinic (Sender)</option>
          <option value="hospital">Main Hospital (Receiver)</option>
        </select>
        
        <button onClick={handleSignup} className="primary-btn">Sign Up</button>
        <div className="link-text">Already have an account? <span onClick={() => navigate('/')}>Login here</span></div>
      </div>
    </div>
  );
}