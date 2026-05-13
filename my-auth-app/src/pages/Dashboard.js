import React, { useEffect, useState } from 'react';
import API from '../api/axios';

const Dashboard = () => {
    const [resData, setResData] = useState({ msg: '', user: null });

    useEffect(() => {
        API.get('authenticated/')
            .then(res => setResData(res.data))
            .catch(err => console.log(err));
    }, []);

    return (
        <div style={{textAlign:'center'}}>
            <h1>{resData.msg || "Welcome to Dashboard"}</h1>
            {resData.user && (
                <div>
                    <p>Welcome: {resData.user.username || resData.user}</p>
                    <p>Email: {resData.user.email}</p>
                    <p>User ID: {resData.user.id}</p>
                </div>
            )}
        </div>
    );
};

export default Dashboard;