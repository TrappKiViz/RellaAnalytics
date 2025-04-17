import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import '../SalesTrendChart/SalesTrendChart.css'; // Reuse chart container CSS
import * as d3 from 'd3-scale-chromatic'; // Import d3-scale-chromatic for color schemes

// Use a more distinct color scheme like Tableau10
const COLORS = d3.schemeTableau10;

// Original light pink/red scheme (for reference)
/*
const COLORS = [
    '#FFCDD2', // Lightest Pink
    '#EF9A9A', 
    '#E57373', 
    '#EF5350', 
    '#F44336', // Medium Red
    '#E53935',
    '#D32F2F',
    '#C62828',
    '#B71C1C', // Darkest Red
    '#FF8A80'  // Coral accent
];
*/

// Accept dataKey prop (e.g., 'value', 'growth', 'count')
const CategorySalesPieChart = ({ data, dataKey = 'value' }) => {
  
  // Determine Title based on dataKey
  const getTitle = (key) => {
      switch(key) {
          case 'value': return 'Sales Distribution by Category';
          case 'growth': return 'Growth Rate Distribution (Mock)';
          case 'count': return 'Transaction Count Distribution (Mock)';
          default: return 'Distribution by Category';
      }
  };

  // Custom Tooltip for Pie Chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload; // The data entry for the hovered slice
      // Format value based on dataKey
      let formattedValue;
      const numericValue = parseFloat(item[dataKey]);
      if (dataKey === 'value' || dataKey === 'profit') { // Format profit as currency too
          formattedValue = numericValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
      } else if (dataKey === 'growth') {
          formattedValue = `${(numericValue * 100).toFixed(1)}%`; // Assuming growth is decimal (e.g., 0.05 for 5%)
      } else { // e.g., count
          formattedValue = numericValue.toLocaleString('en-US');
      }

      return (
        <div className="custom-tooltip chart-tooltip">
          <p className="tooltip-label">{`${item.name}`}</p>
          {/* Display the value corresponding to the dataKey */}
          <p className="tooltip-value">{`${getTitle(dataKey)}: ${formattedValue}`}</p>
          <p className="tooltip-percent">{`(Share: ${(payload[0].percent * 100).toFixed(1)}%)`}</p>
        </div>
      );
    }
    return null;
  };

  if (!data || data.length === 0) {
    return <div className="chart-container chart-placeholder"><span>{getTitle(dataKey)}</span>No data available for selected category metric.</div>;
  }

  return (
    <div className="chart-container pie-chart-container">
        <h3 className="chart-title">{getTitle(dataKey)}</h3>
        <ResponsiveContainer width="100%" height={300}> 
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    // Use dataKey prop here
                    dataKey={dataKey} 
                    nameKey="name"
                    outerRadius={80}
                    fill="#8884d8"
                >
                    {data.map((entry, index) => (
                        // Use modulo operator to cycle through COLORS if there are more categories than colors
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    </div>
  );
};

// Example for custom label (optional)
// const RADIAN = Math.PI / 180;
// const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }) => {
//   const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
//   const x = cx + radius * Math.cos(-midAngle * RADIAN);
//   const y = cy + radius * Math.sin(-midAngle * RADIAN);
//   return (
//     <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
//       {`${name} (${(percent * 100).toFixed(0)}%)`}
//     </text>
//   );
// };

export default CategorySalesPieChart; 