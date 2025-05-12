import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Divider,
  CircularProgress,
  Alert,
  AlertTitle,
  Button,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { formatCurrency, formatPercentage } from './common/ProfitCard';
import { saveAs } from 'file-saver';

function arrayToCSV(data) {
  if (!data.length) return '';
  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(',')];
  for (const row of data) {
    csvRows.push(headers.map(h => JSON.stringify(row[h] ?? '')).join(','));
  }
  return csvRows.join('\n');
}

function downloadCSV(data, filename = 'data.csv') {
  const csv = arrayToCSV(data);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  saveAs(blob, filename);
}

function ProfitOverview() {
  const { loading, error, kpiData } = useOutletContext();
  console.log('ProfitOverview loading:', loading);
  console.log('ProfitOverview error:', error);
  console.log('ProfitOverview kpiData:', kpiData);

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

  if (!kpiData) {
    return (
      <Alert severity="info">
        <AlertTitle>No Data</AlertTitle>
        No overview data available for the selected period.
      </Alert>
    );
  }

  // Use the data directly from the API with fallbacks
  const summary = {
    totalRevenue: kpiData.total_sales || 0,
    totalProfit: kpiData.total_profit || 0,
    averageMargin: kpiData.profit_margin || 0,
  };

  // Find top performers from the API data with validation
  const validItems = kpiData.items?.filter(item => 
    item && 
    typeof item.name === 'string' && 
    typeof item.type === 'string' && 
    typeof item.total_profit === 'number'
  ) || [];

  const topProducts = validItems
    .filter(item => item.type === 'product')
    .sort((a, b) => b.total_profit - a.total_profit)
    .slice(0, 5);

  const topServices = validItems
    .filter(item => item.type === 'service')
    .sort((a, b) => b.total_profit - a.total_profit)
    .slice(0, 5);

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card className="glass-card">
            <CardContent>
              <Typography variant="h6" gutterBottom>Total Revenue</Typography>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatCurrency(summary.totalRevenue)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all products and services
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card className="glass-card">
            <CardContent>
              <Typography variant="h6" gutterBottom>Total Profit</Typography>
              <Typography 
                variant="h4" 
                sx={{ 
                  mb: 1,
                  color: summary.totalProfit >= 0 ? 'success.main' : 'error.main',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}
              >
                {formatCurrency(summary.totalProfit)}
                {summary.totalProfit >= 0 ? (
                  <TrendingUpIcon color="success" />
                ) : (
                  <TrendingDownIcon color="error" />
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Net profit after costs
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card className="glass-card">
            <CardContent>
              <Typography variant="h6" gutterBottom>Average Margin</Typography>
              <Typography 
                variant="h4" 
                sx={{ 
                  mb: 1,
                  color: summary.averageMargin >= 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatPercentage(summary.averageMargin)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Average profit margin across all items
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Performers */}
      <Grid container spacing={3}>
        {/* Top Products */}
        <Grid item xs={12} md={6}>
          <Card className="glass-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6" gutterBottom>Top Performing Products</Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => downloadCSV(
                    validItems.filter(item => item.type === 'product').sort((a, b) => b.total_profit - a.total_profit),
                    'products.csv')}
                >
                  Download CSV
                </Button>
              </Box>
              {topProducts.length > 0 ? (
                topProducts.map((product, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">
                      {product.name}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Profit: {formatCurrency(product.total_profit)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Margin: {formatPercentage(product.profit_margin)}
                      </Typography>
                    </Box>
                    {index < topProducts.length - 1 && <Divider sx={{ mt: 2 }} />}
                  </Box>
                ))
              ) : (
                <Typography color="text.secondary">No product data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top Services */}
        <Grid item xs={12} md={6}>
          <Card className="glass-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6" gutterBottom>Top Performing Services</Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => downloadCSV(
                    validItems.filter(item => item.type === 'service').sort((a, b) => b.total_profit - a.total_profit),
                    'services.csv')}
                >
                  Download CSV
                </Button>
              </Box>
              {topServices.length > 0 ? (
                topServices.map((service, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">
                      {service.name}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Profit: {formatCurrency(service.total_profit)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Margin: {formatPercentage(service.profit_margin)}
                      </Typography>
                    </Box>
                    {index < topServices.length - 1 && <Divider sx={{ mt: 2 }} />}
                  </Box>
                ))
              ) : (
                <Typography color="text.secondary">No service data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default ProfitOverview; 