import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { formatCurrency } from './ProfitCard'; // Import the currency formatter

// Register necessary Chart.js components for Doughnut
ChartJS.register(ArcElement, ChartTooltip, Legend);

function RevenueTypeDoughnutChart({ profitabilityData }) {
  // Calculate total revenue for products and services
  let productRevenue = 0;
  let serviceRevenue = 0;

  if (profitabilityData) {
    Object.values(profitabilityData).forEach(item => {
      if (item.type === 'product') {
        productRevenue += item.sales || 0;
      } else if (item.type === 'service') {
        serviceRevenue += item.sales || 0;
      }
    });
  }

  const chartData = {
    labels: ['Product Revenue', 'Service Revenue'],
    datasets: [
      {
        label: 'Revenue Breakdown',
        data: [productRevenue, serviceRevenue],
        backgroundColor: [
          'rgba(54, 162, 235, 0.7)', // Blue for Products
          'rgba(75, 192, 192, 0.7)', // Green for Services
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom', // Position legend below the chart
      },
      title: {
        display: true,
        text: 'Revenue Contribution by Type',
        font: {
            size: 16,
        },
        padding: {
            bottom: 15,
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed !== null) {
              // Calculate percentage
              const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
              const value = context.parsed;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              label += `${formatCurrency(value)} (${percentage}%)`;
            }
            return label;
          }
        }
      }
    },
  };

  // Avoid rendering chart if data is zero to prevent Chart.js errors/warnings
  if (productRevenue === 0 && serviceRevenue === 0) {
     return (
        <div className="bg-white shadow-md rounded-lg p-4 md:p-6 h-80 md:h-96 flex items-center justify-center text-gray-500">
            No revenue data to display chart.
        </div>
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-4 md:p-6 h-80 md:h-96"> {/* Consistent height */}
      <Doughnut data={chartData} options={options} />
    </div>
  );
}

export default RevenueTypeDoughnutChart; 