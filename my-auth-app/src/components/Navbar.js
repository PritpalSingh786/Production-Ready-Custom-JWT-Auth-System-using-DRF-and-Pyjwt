import { Link } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '../features/auth/authSlice';
import API from '../api/axios';

const Navbar = () => {
    const { isAuthenticated } = useSelector(state => state.auth);
    const dispatch = useDispatch();

    const handleLogout = async () => {
        try {
            await API.post('logout/', { platform: 'web' });
            dispatch(logout());
        } catch (e) { 
            dispatch(logout()); 
        }
    };

    return (
        <nav className="navbar">
            <Link to="/" style={{color:'white', textDecoration:'none'}}>AuthApp</Link>

            <div className="nav-links">
                {isAuthenticated ? (
                    <>
                        <Link to="/dashboard">Dashboard</Link>

                        {/* 🔥 FIXED */}
                        <button onClick={handleLogout} className="logout-btn">
                            Logout
                        </button>
                    </>
                ) : (
                    <>
                        <Link to="/login">Login</Link>
                        <Link to="/register">Register</Link>
                    </>
                )}
            </div>
        </nav>
    );
};

export default Navbar;