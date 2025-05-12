import React, { useState, useEffect } from 'react';
import {
  Routes,
  Route,
  Navigate, // For redirection
  Outlet // For nested routes within layout
} from 'react-router-dom';

// import DashboardPage from './pages/DashboardPage/DashboardPage'; // REMOVE
import LoginPage from './pages/LoginPage/LoginPage'; // Import LoginPage
// import MapViewPage from './pages/MapViewPage/MapViewPage'; // REMOVE
// Import other pages
import ReportsPage from './pages/ReportsPage/ReportsPage';
import SettingsPage from './pages/SettingsPage/SettingsPage';
import Sidebar from './components/Sidebar/Sidebar'; // Corrected path
import Header from './components/Header/Header'; // Assuming Header exists
// import ProfitabilityAnalyticsPage from './pages/ProfitabilityAnalyticsPage.jsx'; // <-- Old page import

// --- Import Profit Analytics Components ---
import ProfitAnalyticsLayout from './components/profit-analytics/ProfitAnalyticsLayout';
import ProfitOverview from './components/profit-analytics/ProfitOverview';
import ProductProfitability from './components/profit-analytics/ProductProfitability';
import ServiceProfitability from './components/profit-analytics/ServiceProfitability';
import DiscountImpact from './components/profit-analytics/DiscountImpact';
import MarginTrends from './components/profit-analytics/MarginTrends';
// --- End Profit Analytics Imports ---

import './index.css';
// import { checkAuthStatus, logout } from './services/api'; // Import auth functions

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
           <Outlet /> {/* Child routes render here */}
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
    return <div className="flex justify-center items-center h-screen"><div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-500"></div></div>; // Fixed className
  }

  return (
    <Routes>
      {/* Public Login Route */}
      <Route 
         path="/login" 
         element={isLoggedIn ? <Navigate to="/profitability" /> : <LoginPage onLoginSuccess={handleLoginSuccess} />} // Redirect to /profitability
      />
      
      {/* Protected Routes within Layout */}
      <Route element={<ProtectedLayout isLoggedIn={isLoggedIn} onLogout={handleLogout} />}>
          {/* <Route path="/" element={<DashboardPage />} /> REMOVE */}
          {/* <Route path="/map" element={<MapViewPage />} /> REMOVE */}
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          
          {/* --- Profit Analytics Nested Routes --- */}
          <Route path="/profitability" element={<ProfitAnalyticsLayout />}>
            <Route index element={<ProfitOverview />} />
            <Route path="overview" element={<ProfitOverview />} />
            <Route path="products" element={<ProductProfitability />} />
            <Route path="services" element={<ServiceProfitability />} />
            <Route path="discounts" element={<DiscountImpact />} />
            <Route path="trends" element={<MarginTrends />} />
             {/* Optional: Add a redirect or default for unknown sub-paths */}
             <Route path="*" element={<Navigate to="overview" replace />} /> 
          </Route>
          {/* --- End Profit Analytics Routes --- */}

          {/* Redirect unknown top-level protected routes to /profitability */}
          <Route path="*" element={<Navigate to="/profitability" replace />} /> 
      </Route>

    </Routes>
  );
}

export default App; 