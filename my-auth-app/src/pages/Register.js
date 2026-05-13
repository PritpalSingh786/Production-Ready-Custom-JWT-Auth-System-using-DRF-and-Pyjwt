import React, { useState } from 'react';
import API from '../api/axios';
import { useNavigate } from 'react-router-dom';

const Register = () => {
    const [form, setForm] = useState({ username: '', email: '', password: '' });
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await API.post('register/', form);
            alert("Registration Success! Please check email to verify.");
            navigate('/login');
        } catch (err) { alert(JSON.stringify(err.response.data)); }
    };

    return (
        <div className="container">
            <h2>Register</h2>
            <form onSubmit={handleSubmit}>
                <input type="text" placeholder="Username" onChange={e => setForm({...form, username: e.target.value})} />
                <input type="email" placeholder="Email" onChange={e => setForm({...form, email: e.target.value})} />
                <input type="password" placeholder="Password" onChange={e => setForm({...form, password: e.target.value})} />
                <button type="submit">Sign Up</button>
            </form>
        </div>
    );
};
export default Register;