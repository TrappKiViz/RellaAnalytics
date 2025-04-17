import React from 'react';
import './TopItemsTable.css';

const TopItemsTable = ({ title, items, valueKey, valueLabel = 'Value', isCurrency = false }) => {
  // items should be an array of objects, e.g., [{ product_name: 'A', total_sales: 100 }, ...]
  // valueKey should be the key for the numeric value, e.g., 'total_sales'

  const displayItems = items && items.length > 0 ? items : [];

  const formatValue = (value) => {
    if (value === undefined || value === null || value === 'N/A') {
      return 'N/A';
    }
    if (isCurrency) {
      // Basic currency formatting
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    }
    // Could add other formatters here if needed
    return value.toLocaleString(); // Default formatting for numbers
  };

  return (
    <div className="table-container">
      <h4>{title}</h4>
      {displayItems.length > 0 ? (
        <table className="items-table">
          <thead>
            <tr>
              <th>Item Name</th>
              <th>{valueLabel}</th>
            </tr>
          </thead>
          <tbody>
            {displayItems.map((item, index) => (
              <tr key={index}> 
                {/* Attempt to find a name key */} 
                <td>{item.name || item.product_name || item.service_name || 'N/A'}</td>
                <td>{formatValue(item[valueKey])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="no-data-message">No data available.</p>
      )}
    </div>
  );
};

export default TopItemsTable; 