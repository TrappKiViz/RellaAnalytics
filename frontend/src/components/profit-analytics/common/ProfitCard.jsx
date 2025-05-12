import React from 'react';
import { FaDollarSign, FaPercentage, FaChartLine, FaInfoCircle } from 'react-icons/fa'; // Example icons
import { Tooltip } from 'react-tooltip'; // Import Tooltip
import LoadingSpinner from './LoadingSpinner';

// Helper function to format currency
export const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '-'; // Or $0.00, or Loading...
  }
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};

// Helper function to format percentage
export const formatPercentage = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }
  return `${value.toFixed(1)}%`;
};

function ProfitCard({ title, value, format = 'currency', icon: Icon, isLoading, tooltipText }) {
  const displayValue = isLoading
    ? <LoadingSpinner size="small" />
    : format === 'percentage'
    ? formatPercentage(value)
    : formatCurrency(value);

  const tooltipId = `tooltip-${title.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <div className="bg-white shadow-md rounded-lg p-4 md:p-5 relative hover:shadow-lg transition-shadow duration-200 ease-in-out">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wider flex items-center">
          {title}
          {tooltipText && (
            <FaInfoCircle
              data-tooltip-id={tooltipId}
              data-tooltip-content={tooltipText}
              className="ml-2 text-gray-400 hover:text-gray-600 cursor-help"
            />
          )}
        </h3>
        {Icon && <Icon className="h-5 w-5 text-gray-400" />}
      </div>
      <div className="mt-1 text-2xl md:text-3xl font-semibold text-gray-900">
        {displayValue}
      </div>
      {/* Tooltip Component - Placed once, used by multiple cards via ID */}
      {tooltipText && <Tooltip id={tooltipId} place="top" effect="solid" className="max-w-xs text-xs !bg-gray-700 !text-white" />}
    </div>
  );
}

export default ProfitCard; 