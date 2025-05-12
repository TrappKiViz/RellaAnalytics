import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../Header/Header';
import Sidebar from '../Sidebar/Sidebar';
import './Layout.css'; // Basic CSS for layout structure
import logo from '../../../backend/d1c2e2b5-5d5b-4a9b-8a2e-65d44d169166.png';

const Layout = () => {
  return (
    <div className="app-layout">
      <Header />
      <div className="app-main">
        <Sidebar />
        <main className="app-content">
          <Outlet /> {/* Page content will be rendered here */}
        </main>
      </div>
    </div>
  );
};

export default Layout; 