import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
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
} from 'recharts';
import { formatCurrency, formatPercentage } from './common/ProfitCard';

function MarginTrends() {
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
        No margin trend data available for the selected period.
      </Alert>
    );
  }

  // Format data for the chart
  const chartData = kpiData.trends
    .filter(trend => trend && typeof trend.date === 'string') // Filter out invalid data
    .map(trend => ({
      date: new Date(trend.date).toLocaleDateString(),
      margin: trend.profit_margin || 0,
      revenue: trend.sales || 0,
      profit: trend.profit || 0,
    }))
    .sort((a, b) => new Date(a.date) - new Date(b.date)); // Ensure data is sorted by date

  if (chartData.length === 0) {
    return (
      <Alert severity="warning">
        <AlertTitle>Invalid Data</AlertTitle>
        The trend data appears to be in an invalid format.
      </Alert>
    );
  }

  // Calculate summary statistics
  const avgMargin = chartData.reduce((sum, day) => sum + day.margin, 0) / chartData.length;
  const highestMargin = Math.max(...chartData.map(day => day.margin));
  const lowestMargin = Math.min(...chartData.map(day => day.margin));

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Margin Trends Over Time
              </Typography>
              <Box sx={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                  <LineChart data={chartData}>
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
                    <Line
                      yAxisId="margin"
                      type="monotone"
                      dataKey="margin"
                      name="Margin %"
                      stroke="#8884d8"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue"
                      stroke="#82ca9d"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="profit"
                      name="Profit"
                      stroke="#ffc658"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Summary Statistics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Average Margin
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(avgMargin)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Highest Margin
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(highestMargin)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Lowest Margin
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(lowestMargin)}
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

export default MarginTrends; 