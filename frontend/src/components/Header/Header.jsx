import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="app-header">
      <img src="/d1c2e2b5-5d5b-4a9b-8a2e-65d44d169166.png" alt="App Logo" style={{ height: '40px', marginRight: '16px' }} />
      <h1>Rella Analytics</h1>
      {/* Placeholder for User Profile / Logout */}
      <div className="user-profile-placeholder">User</div>
    </header>
  );
};

export default Header; 