import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import DataManagementPage from './pages/DataManagementPage';
import CustomerInsightsPage from './pages/CustomerInsightsPage';
import ProfitabilityAnalyticsPage from './pages/ProfitabilityAnalyticsPage';
import PrivateRoute from './components/Auth/PrivateRoute';
import AuthProvider from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected Routes */}
          <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
          <Route path="/data" element={<PrivateRoute><DataManagementPage /></PrivateRoute>} />
          <Route path="/customer-insights" element={<PrivateRoute><CustomerInsightsPage /></PrivateRoute>} />
          <Route path="/profitability" element={<PrivateRoute><ProfitabilityAnalyticsPage /></PrivateRoute>} />
          
          {/* Add other routes here */}
          
          {/* Redirect unknown paths to dashboard (or login if not authenticated) */}
          {/* This needs refinement based on PrivateRoute behavior */}
          <Route path="*" element={<Navigate to="/" replace />} /> 
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App; 