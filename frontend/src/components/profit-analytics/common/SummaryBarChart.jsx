import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip, // Renamed to avoid conflict with react-tooltip
  Legend,
} from 'chart.js';
import { formatCurrency } from './ProfitCard'; // Import the currency formatter

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

function SummaryBarChart({ summaryData }) {
  // Prepare data for the chart
  const chartData = {
    labels: ['Comparison'], // Single category for side-by-side bars
    datasets: [
      {
        label: 'Total Revenue',
        data: [summaryData?.total_revenue || 0],
        backgroundColor: 'rgba(54, 162, 235, 0.6)', // Blue
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      },
      {
        label: 'Total Cost',
        data: [summaryData?.total_cost || 0],
        backgroundColor: 'rgba(255, 99, 132, 0.6)', // Red
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
      },
      {
        label: 'Total Profit',
        data: [summaryData?.total_profit || 0],
        backgroundColor: 'rgba(75, 192, 192, 0.6)', // Green
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  // Configure chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false, // Allow chart to fill container height
    plugins: {
      legend: {
        position: 'top', // Position the legend
      },
      title: {
        display: true,
        text: 'Revenue vs. Cost vs. Profit',
        font: {
            size: 16,
        },
        padding: {
            bottom: 20, // Add space below title
        }
      },
      tooltip: {
         callbacks: {
             label: function(context) {
                 let label = context.dataset.label || '';
                 if (label) {
                     label += ': ';
                 }
                 if (context.parsed.y !== null) {
                     label += formatCurrency(context.parsed.y);
                 }
                 return label;
             }
         }
     }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          // Include a dollar sign in the ticks
          callback: function(value, index, values) {
            return formatCurrency(value);
          }
        },
        title: {
          display: true,
          text: 'Amount (USD)'
        }
      },
       x: {
         // No title needed for the single category
       }
    },
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-4 md:p-6 h-80 md:h-96"> {/* Fixed height */}
      <Bar options={options} data={chartData} />
    </div>
  );
}

export default SummaryBarChart; 