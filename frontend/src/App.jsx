import React from 'react';
import {
  Routes,
  Route
} from 'react-router-dom';

import ReportsPage from './pages/ReportsPage/ReportsPage';
import SettingsPage from './pages/SettingsPage/SettingsPage';
import Sidebar from './components/Sidebar/Sidebar';
import Header from './components/Header/Header';
import ProfitAnalyticsLayout from './components/profit-analytics/ProfitAnalyticsLayout';
import ProfitOverview from './components/profit-analytics/ProfitOverview';
import ProductProfitability from './components/profit-analytics/ProductProfitability';
import ServiceProfitability from './components/profit-analytics/ServiceProfitability';
import DiscountImpact from './components/profit-analytics/DiscountImpact';
import MarginTrends from './components/profit-analytics/MarginTrends';
import './index.css';

function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main>
          <Routes>
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profitability" element={<ProfitAnalyticsLayout />}>
              <Route index element={<ProfitOverview />} />
              <Route path="overview" element={<ProfitOverview />} />
              <Route path="products" element={<ProductProfitability />} />
              <Route path="services" element={<ServiceProfitability />} />
              <Route path="discounts" element={<DiscountImpact />} />
              <Route path="trends" element={<MarginTrends />} />
              <Route path="*" element={<ProfitOverview />} />
            </Route>
            <Route path="*" element={<ProfitOverview />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App; 