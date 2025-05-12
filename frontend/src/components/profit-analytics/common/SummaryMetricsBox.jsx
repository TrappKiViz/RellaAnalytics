import React from 'react';
import { Tooltip } from 'react-tooltip';
import { FaInfoCircle, FaDollarSign, FaPercentage } from 'react-icons/fa';
import LoadingSpinner from './LoadingSpinner';
import { formatCurrency, formatPercentage } from './ProfitCard';

// Helper to generate unique tooltip IDs
const metricTooltipId = (metricName) => `tooltip-metric-${metricName.replace(/\s+/g, '-').toLowerCase()}`;

function SummaryMetricsBox({ summary, loading, tooltips }) {

  const metrics = [
    { 
        key: 'revenue', 
        title: 'Total Revenue', 
        value: summary?.total_revenue, 
        format: 'currency', 
        icon: FaDollarSign, 
        tooltip: tooltips?.revenue 
    },
    { 
        key: 'cost', 
        title: 'Total Cost', 
        value: summary?.total_cost, 
        format: 'currency', 
        icon: FaDollarSign, 
        tooltip: tooltips?.cost 
    },
    { 
        key: 'profit', 
        title: 'Total Profit', 
        value: summary?.total_profit, 
        format: 'currency', 
        icon: FaDollarSign, 
        tooltip: tooltips?.profit 
    },
    { 
        key: 'margin', 
        title: 'Profit Margin', 
        value: summary?.profit_margin_percentage, 
        format: 'percentage', 
        icon: FaPercentage, 
        tooltip: tooltips?.margin 
    },
  ];

  return (
    <div className="bg-white shadow-md rounded-lg p-5 md:p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Key Performance Indicators</h2>
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-300 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-y-4 gap-x-6">
          {metrics.map(metric => {
            const Icon = metric.icon;
            const displayValue = metric.format === 'percentage'
              ? formatPercentage(metric.value)
              : formatCurrency(metric.value);
            const tooltipId = metricTooltipId(metric.key);

            return (
              <div key={metric.key}>
                <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wider flex items-center mb-1">
                  {metric.title}
                  {metric.tooltip && (
                    <FaInfoCircle
                      data-tooltip-id={tooltipId}
                      data-tooltip-content={metric.tooltip}
                      className="ml-1.5 text-gray-400 hover:text-gray-600 cursor-help"
                    />
                  )}
                </h3>
                <p className="text-2xl font-semibold text-gray-900 flex items-center">
                  {Icon && <Icon className="h-5 w-5 text-indigo-500 mr-2 opacity-75" />} 
                  {displayValue}
                </p>
                {metric.tooltip && <Tooltip id={tooltipId} place="top" effect="solid" className="max-w-xs text-xs !bg-gray-700 !text-white" />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default SummaryMetricsBox; 