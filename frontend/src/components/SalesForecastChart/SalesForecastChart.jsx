import React from 'react';
import {
  LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import '../SalesTrendChart/SalesTrendChart.css'; // Reuse chart container CSS

// Custom Tooltip for combined chart
const ForecastTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const point = payload[0].payload;
    let tooltipContent = `<div class="custom-tooltip">
                            <p class="label">Date: ${label}</p>`;
    
    if (point.sales !== undefined && point.sales !== null) {
      tooltipContent += `<p style="color:${payload[0].color}">Actual Sales: $${point.sales.toLocaleString()}</p>`;
    }
    if (point.mean !== undefined && point.mean !== null) {
        tooltipContent += `<p style="color:${payload.find(p=>p.dataKey==='mean')?.color || '#82ca9d'}">Forecast: $${point.mean.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>`;
        if (point.mean_ci_lower !== undefined) {
             tooltipContent += `<p style="font-size: 0.8em; color:#888;"> (95% CI: $${point.mean_ci_lower.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} - $${point.mean_ci_upper.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})})</p>`;
        }
    }
    tooltipContent += `</div>`;
    // Use dangerouslySetInnerHTML carefully if needed, or parse and render React elements
    // For simplicity here, just returning a string, but a React component is safer.
    // A simple approach is to just show the key fields:
    return (
      <div className="custom-tooltip">
        <p className="label">{`Date: ${label}`}</p>
        {point.sales !== undefined && <p style={{ color: '#d1365f' }}>{`Actual: $${point.sales.toLocaleString()}`}</p>}
        {point.mean !== undefined && <p style={{ color: '#82ca9d' }}>{`Forecast: $${point.mean.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</p>}
        {point.mean_ci_lower !== undefined && <p style={{ fontSize: '0.8em', color:'#888' }}>{`(95% CI: $${point.mean_ci_lower.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} - $${point.mean_ci_upper.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})})`}</p>}
      </div>
    );

  }
  return null;
};

const SalesForecastChart = ({ historicalData, forecastData, note }) => {
  // Combine historical and forecast data for the chart
  // Ensure forecast points don't overwrite historical ones
  const combinedData = historicalData.map(h => ({ ...h })); // Copy historical
  
  if (forecastData && forecastData.length > 0) {
    const historicalDates = new Set(historicalData.map(h => h.date));
    forecastData.forEach(f => {
      // Add forecast point if its date is not already in the historical set
      if (!historicalDates.has(f.date)) {
          // Check if date ALREADY exists in combinedData (from a previous forecast point - unlikely but safe)
          const existingIndex = combinedData.findIndex(c => c.date === f.date);
          if (existingIndex === -1) {
              combinedData.push({
                  date: f.date, 
                  mean: f.mean, 
                  mean_ci_lower: f.mean_ci_lower, 
                  mean_ci_upper: f.mean_ci_upper 
              });
          } // else: Skip if somehow already added
      } else {
          // If date exists in historical data, find it and ADD forecast values
          const existingDataPoint = combinedData.find(c => c.date === f.date);
          if (existingDataPoint) {
              existingDataPoint.mean = f.mean;
              existingDataPoint.mean_ci_lower = f.mean_ci_lower;
              existingDataPoint.mean_ci_upper = f.mean_ci_upper;
          } else {
              // Should not happen if historicalDates.has(f.date) is true
              console.error("Logic error: Historical date not found in combinedData", f.date);
          }
      }
    });
    // Ensure data is sorted by date after merging
    combinedData.sort((a, b) => new Date(a.date) - new Date(b.date));
  }

  const hasData = combinedData.length > 0;

  return (
    <div className="chart-container">
      <h4>Sales Forecast (Illustrative)</h4>
      {note && <p className="chart-note">{note}</p>}
      <div className="chart-area actual-chart">
        {hasData ? (
          <ResponsiveContainer width="100%" height={300}> 
            <LineChart data={combinedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
              <XAxis dataKey="date" stroke="#555" />
              <YAxis stroke="#555" tickFormatter={(value) => `$${value.toLocaleString()}`} />
              <Tooltip content={<ForecastTooltip />} />
              <Legend />
              {/* Historical Sales Line */}
              <Line type="monotone" dataKey="sales" name="Actual Sales" stroke="#d1365f" strokeWidth={2} dot={false} activeDot={{ r: 6 }} connectNulls={false} />
              {/* Forecast Line */}
              <Line type="monotone" dataKey="mean" name="Forecast" stroke="#82ca9d" strokeWidth={2} dot={false} activeDot={{ r: 6 }} connectNulls={false} />
              {/* Confidence Interval Area */}
              <Area type="monotone" dataKey="mean_ci_upper" name="95% CI Upper" stroke={false} fill="#82ca9d" fillOpacity={0.2} connectNulls={false} />
              <Area type="monotone" dataKey="mean_ci_lower" name="95% CI Lower" stroke={false} fill="#82ca9d" fillOpacity={0.2} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p>No forecast data available.</p>
        )}
      </div>
    </div>
  );
};

export default SalesForecastChart; 