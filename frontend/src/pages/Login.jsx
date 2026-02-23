import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [formData, setFormData] = useState({ username: '', password: '', role: 'rural' });
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/login`, formData);
      
      if (res.data.role !== formData.role) {
        alert(`Role Mismatch: You registered as "${res.data.role}". Please switch role.`);
        return;
      }

      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      localStorage.setItem('username', formData.username);
      navigate('/dashboard');
    } catch (e) {
      alert("Login Failed: Check credentials.");
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="text-blue text-center">TelePath AI</h1>
        <p className="text-center" style={{color:'#94a3b8', marginBottom:'20px'}}>Secure Login</p>
        
        <input className="login-input" placeholder="Username" onChange={e => setFormData({...formData, username: e.target.value})} />
        <input className="login-input" type="password" placeholder="Password" onChange={e => setFormData({...formData, password: e.target.value})} />
        
        <select className="login-select" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
          <option value="rural">Rural Clinic</option>
          <option value="hospital">Main Hospital</option>
        </select>
        
        <button onClick={handleLogin} className="primary-btn">Login</button>
        <div className="link-text">New clinic? <span onClick={() => navigate('/signup')}>Create account</span></div>
      </div>
    </div>
  );
}