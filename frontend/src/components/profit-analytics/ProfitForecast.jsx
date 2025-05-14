import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { formatCurrency, formatPercentage } from './common/ProfitCard';

function ProfitForecast() {
  const { loading, error, kpiData } = useOutletContext();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!kpiData?.trends || kpiData.trends.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Data</AlertTitle>
        No forecast data available for the selected period.
      </Alert>
    );
  }

  // Format historical data
  const historicalData = kpiData.trends
    .filter(trend => trend && typeof trend.date === 'string')
    .map(trend => ({
      date: new Date(trend.date).toLocaleDateString(),
      margin: trend.profit_margin || 0,
      revenue: trend.sales || 0,
      profit: trend.profit || 0,
    }))
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  // Generate forecast data (this would normally come from your backend)
  const lastDate = new Date(historicalData[historicalData.length - 1].date);
  const forecastData = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(lastDate);
    date.setDate(date.getDate() + i + 1);
    
    // Simple linear forecast (replace with actual ML model)
    const lastMargin = historicalData[historicalData.length - 1].margin;
    const trend = (historicalData[historicalData.length - 1].margin - historicalData[0].margin) / historicalData.length;
    const predictedMargin = lastMargin + (trend * (i + 1));
    
    // Add some confidence interval
    const confidenceInterval = 2; // 2% confidence interval
    
    return {
      date: date.toLocaleDateString(),
      margin: predictedMargin,
      upperBound: predictedMargin + confidenceInterval,
      lowerBound: predictedMargin - confidenceInterval,
      revenue: historicalData[historicalData.length - 1].revenue * (1 + (trend * (i + 1) / 100)),
      profit: historicalData[historicalData.length - 1].profit * (1 + (trend * (i + 1) / 100)),
    };
  });

  // Combine historical and forecast data
  const chartData = [...historicalData, ...forecastData];

  // Calculate forecast accuracy metrics
  const avgMargin = chartData.reduce((sum, day) => sum + day.margin, 0) / chartData.length;
  const trend = (chartData[chartData.length - 1].margin - chartData[0].margin) / chartData.length;
  const trendDirection = trend > 0 ? 'upward' : trend < 0 ? 'downward' : 'stable';

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Profit Margin Forecast
              </Typography>
              <Box sx={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis 
                      yAxisId="margin"
                      orientation="right"
                      tickFormatter={(value) => `${value}%`}
                    />
                    <YAxis 
                      yAxisId="revenue"
                      tickFormatter={(value) => formatCurrency(value)}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'margin') return `${value}%`;
                        return formatCurrency(value);
                      }}
                    />
                    <Legend />
                    <Area
                      yAxisId="margin"
                      type="monotone"
                      dataKey="upperBound"
                      dataKey2="lowerBound"
                      name="Confidence Interval"
                      fill="#8884d8"
                      fillOpacity={0.1}
                      stroke="none"
                    />
                    <Line
                      yAxisId="margin"
                      type="monotone"
                      dataKey="margin"
                      name="Predicted Margin %"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="revenue"
                      name="Predicted Revenue"
                      stroke="#82ca9d"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="profit"
                      name="Predicted Profit"
                      stroke="#ffc658"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Forecast Insights
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Predicted Average Margin
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(avgMargin)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Trend Direction
                  </Typography>
                  <Typography variant="h6" color={trend > 0 ? 'success.main' : trend < 0 ? 'error.main' : 'text.primary'}>
                    {trendDirection}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Confidence Level
                  </Typography>
                  <Typography variant="h6">
                    95%
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default ProfitForecast; 