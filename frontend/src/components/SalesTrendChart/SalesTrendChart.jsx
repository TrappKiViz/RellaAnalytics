import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './SalesTrendChart.css';

// Custom Tooltip Content
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{`Date: ${label}`}</p>
        <p className="intro">{`Sales: $${payload[0].value.toLocaleString()}`}</p>
        {/* <p className="desc">Anything else you want</p> */}
      </div>
    );
  }
  return null;
};

const SalesTrendChart = ({ data }) => {
  // Expect data in format: [{ date: 'YYYY-MM-DD' or 'YYYY-Qx', sales: number }, ...]

  // Basic check for data
  const hasData = data && data.length > 0;

  return (
    <div className="chart-container">
      <h4>Sales Trend</h4>
      <div className="chart-area actual-chart">
        {hasData ? (
          <ResponsiveContainer width="100%" height={250}> 
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#fccdd3" />
              <XAxis dataKey="date" stroke="#555" />
              <YAxis stroke="#555" tickFormatter={(value) => `$${value.toLocaleString()}`} />
              <Tooltip content={<CustomTooltip />} />
              {/* <Legend /> */}{/* Optional */}
              <Line type="monotone" dataKey="sales" stroke="#d1365f" strokeWidth={2} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p>No sales trend data available.</p>
        )}
      </div>
    </div>
  );
};

export default SalesTrendChart; 