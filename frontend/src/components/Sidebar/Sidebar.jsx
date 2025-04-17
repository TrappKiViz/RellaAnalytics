import React from 'react';
import { NavLink } from 'react-router-dom'; // Use NavLink for active styling
import './Sidebar.css';

const Sidebar = () => {
  return (
    <aside className="app-sidebar">
      <nav>
        <ul>
          <li>
            {/* NavLink adds 'active' class automatically */}
            <NavLink to="/" end> {/* 'end' prop matches exact root path */}
              Dashboard
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
          <li>
            <NavLink to="/map">Map View</NavLink>
          </li>
          {/* Add more links as needed */}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar; 