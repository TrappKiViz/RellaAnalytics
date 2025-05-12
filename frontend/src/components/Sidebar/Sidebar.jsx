import React from 'react';
import { NavLink } from 'react-router-dom'; // Use NavLink for active styling
import './Sidebar.css';

const Sidebar = ({ onLogout }) => {
  return (
    <aside className="app-sidebar">
      <nav>
        <ul>
          {/*<li>
             Removed Dashboard Link 
            <NavLink to="/" end> 
              Dashboard
            </NavLink>
          </li>*/}
          <li>
            <NavLink to="/profitability" end> {/* Point default here? */}
              Profit Analytics
            </NavLink>
          </li>
          <li>
            <NavLink to="/reports">
              Reports
            </NavLink>
          </li>
          <li>
            <NavLink to="/settings">
              Settings
            </NavLink>
          </li>
          {/*<li>
             Removed Map View Link 
            <NavLink to="/map">Map View</NavLink>
          </li>*/}
          
          {/* Add more links as needed */}
        </ul>
      </nav>
      {/* Logout Button (Example) */}
      <div className="sidebar-logout">
        <button onClick={onLogout}>Logout</button>
      </div>
    </aside>
  );
};

export default Sidebar; 