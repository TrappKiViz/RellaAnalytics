import React from 'react';
import './KPI_Card.css';

const KPI_Card = ({ title, value, unit = '' }) => {
  // Basic check for loading/placeholder state
  const displayValue = value !== undefined && value !== null ? `${unit}${value}` : '...';

  return (
    <div className="kpi-card-component">
      <h4 className="kpi-title">{title}</h4>
      <p className="kpi-value">{displayValue}</p>
    </div>
  );
};

export default KPI_Card; 