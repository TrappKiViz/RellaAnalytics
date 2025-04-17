import React, { useState, useEffect } from 'react';
import {
  Routes,
  Route,
  Navigate, // For redirection
  Outlet // For nested routes within layout
} from 'react-router-dom';

import DashboardPage from './pages/DashboardPage/DashboardPage';
import LoginPage from './pages/LoginPage/LoginPage'; // Import LoginPage
import MapViewPage from './pages/MapViewPage/MapViewPage'; // Import MapViewPage
// Import other pages
import ReportsPage from './pages/ReportsPage/ReportsPage';
import SettingsPage from './pages/SettingsPage/SettingsPage';
import Sidebar from './components/Sidebar/Sidebar'; // Assuming Sidebar exists
import Header from './components/Header/Header'; // Assuming Header exists

import './index.css';
import { checkAuthStatus, logout } from './services/api'; // Import auth functions

// Protected Route Component
const ProtectedLayout = ({ isLoggedIn, onLogout }) => {
  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar onLogout={onLogout} /> {/* Pass logout handler */}
      <div className="main-content">
        <Header /> {/* Add a simple header if needed */}
        <main>
           <Outlet /> {/* Child routes (Dashboard, Reports, Settings) render here */}
        </main>
      </div>
    </div>
  );
};


function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(null); // null: checking, true: logged in, false: not logged in

  // Check auth status on initial load
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const data = await checkAuthStatus();
        setIsLoggedIn(data.isLoggedIn);
      } catch (error) {
        console.error("Auth check failed:", error);
        setIsLoggedIn(false); // Assume not logged in if check fails
      }
    };
    checkStatus();
  }, []);

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
        console.error("Logout failed:", error);
        // Still update state even if API fails
    } finally {
        setIsLoggedIn(false);
    }
  };

  // Show loading indicator while checking auth status
  if (isLoggedIn === null) {
    return <div>Loading...</div>; // Or a proper loading spinner
  }

  return (
    <Routes>
      {/* Public Login Route */}
      <Route 
         path="/login" 
         element={isLoggedIn ? <Navigate to="/" /> : <LoginPage onLoginSuccess={handleLoginSuccess} />} 
      />
      
      {/* Protected Routes within Layout */}
      <Route element={<ProtectedLayout isLoggedIn={isLoggedIn} onLogout={handleLogout} />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/map" element={<MapViewPage />} />
          {/* Add routes for Reports and Settings */}
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          {/* Add a catch-all or redirect for unknown protected routes if needed */}
          <Route path="*" element={<Navigate to="/" replace />} /> 
      </Route>

    </Routes>
  );
}

export default App; 