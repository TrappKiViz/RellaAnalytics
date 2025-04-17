import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import { login } from '../../services/api'; // Import the actual login function

// Replace with actual API call from services/api.js later
// const loginUser = async (credentials) => {
//     const response = await fetch('/api/v1/auth/login', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify(credentials),
//     });
//     if (!response.ok) {
//         const errorData = await response.json().catch(() => ({}));
//         throw new Error(errorData.message || 'Login failed');
//     }
//     return response.json(); // e.g., { success: true, message: 'Logged in' }
// };

const LoginPage = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            // await loginUser({ username, password }); // Use the imported function
            await login({ username, password }); // Corrected line
            // Call the function passed from App to update the auth state
            if (onLoginSuccess) {
                 onLoginSuccess();
            }
            navigate('/'); // Navigate to dashboard after successful login
        } catch (err) {
            setError(err.message);
            setIsLoading(false);
        }
        // No need to setIsLoading(false) on success because we navigate away
    };

    return (
        <div className="login-page-container">
            <div className="login-box">
                <h2>Rella Analytics Login</h2>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label htmlFor="username">Username</label>
                        <input 
                            type="text" 
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required 
                            disabled={isLoading}
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <input 
                            type="password" 
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required 
                            disabled={isLoading}
                        />
                    </div>
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Logging in...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LoginPage; 