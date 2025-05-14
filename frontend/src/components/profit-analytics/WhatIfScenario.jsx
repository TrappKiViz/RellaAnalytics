import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Slider,
  TextField,
  Button,
  Alert,
  AlertTitle,
  CircularProgress,
  Divider,
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

function WhatIfScenario() {
  const { loading, error, kpiData } = useOutletContext();
  const [priceAdjustment, setPriceAdjustment] = useState(0);
  const [costAdjustment, setCostAdjustment] = useState(0);
  const [volumeAdjustment, setVolumeAdjustment] = useState(0);

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

  if (!kpiData?.items || kpiData.items.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Data</AlertTitle>
        No data available for scenario analysis.
      </Alert>
    );
  }

  // Calculate baseline metrics
  const baselineMetrics = {
    revenue: kpiData.total_sales || 0,
    cost: kpiData.total_cost || 0,
    profit: kpiData.total_profit || 0,
    margin: kpiData.profit_margin || 0,
  };

  // Calculate adjusted metrics
  const adjustedMetrics = {
    revenue: baselineMetrics.revenue * (1 + priceAdjustment / 100) * (1 + volumeAdjustment / 100),
    cost: baselineMetrics.cost * (1 + costAdjustment / 100) * (1 + volumeAdjustment / 100),
  };
  adjustedMetrics.profit = adjustedMetrics.revenue - adjustedMetrics.cost;
  adjustedMetrics.margin = (adjustedMetrics.profit / adjustedMetrics.revenue) * 100;

  // Prepare data for comparison chart
  const comparisonData = [
    {
      name: 'Baseline',
      revenue: baselineMetrics.revenue,
      cost: baselineMetrics.cost,
      profit: baselineMetrics.profit,
      margin: baselineMetrics.margin,
    },
    {
      name: 'Adjusted',
      revenue: adjustedMetrics.revenue,
      cost: adjustedMetrics.cost,
      profit: adjustedMetrics.profit,
      margin: adjustedMetrics.margin,
    },
  ];

  const handleReset = () => {
    setPriceAdjustment(0);
    setCostAdjustment(0);
    setVolumeAdjustment(0);
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Scenario Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scenario Controls
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Price Adjustment (%)</Typography>
                  <Slider
                    value={priceAdjustment}
                    onChange={(_, value) => setPriceAdjustment(value)}
                    min={-50}
                    max={50}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Cost Adjustment (%)</Typography>
                  <Slider
                    value={costAdjustment}
                    onChange={(_, value) => setCostAdjustment(value)}
                    min={-50}
                    max={50}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Volume Adjustment (%)</Typography>
                  <Slider
                    value={volumeAdjustment}
                    onChange={(_, value) => setVolumeAdjustment(value)}
                    min={-50}
                    max={50}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={handleReset}>
                  Reset Scenario
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Impact Summary */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scenario Impact
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Revenue Impact
                  </Typography>
                  <Typography variant="h6" color={adjustedMetrics.revenue >= baselineMetrics.revenue ? 'success.main' : 'error.main'}>
                    {formatCurrency(adjustedMetrics.revenue - baselineMetrics.revenue)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Cost Impact
                  </Typography>
                  <Typography variant="h6" color={adjustedMetrics.cost <= baselineMetrics.cost ? 'success.main' : 'error.main'}>
                    {formatCurrency(adjustedMetrics.cost - baselineMetrics.cost)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Profit Impact
                  </Typography>
                  <Typography variant="h6" color={adjustedMetrics.profit >= baselineMetrics.profit ? 'success.main' : 'error.main'}>
                    {formatCurrency(adjustedMetrics.profit - baselineMetrics.profit)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Margin Impact
                  </Typography>
                  <Typography variant="h6" color={adjustedMetrics.margin >= baselineMetrics.margin ? 'success.main' : 'error.main'}>
                    {formatPercentage(adjustedMetrics.margin - baselineMetrics.margin)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Comparison Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Comparison Chart
              </Typography>
              <Box sx={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                  <LineChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis yAxisId="left" tickFormatter={formatCurrency} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                    <Tooltip
                      formatter={(value, name) => {
                        if (name === 'margin') return `${value}%`;
                        return formatCurrency(value);
                      }}
                    />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="revenue" name="Revenue" stroke="#82ca9d" />
                    <Line yAxisId="left" type="monotone" dataKey="cost" name="Cost" stroke="#ff8042" />
                    <Line yAxisId="left" type="monotone" dataKey="profit" name="Profit" stroke="#8884d8" />
                    <Line yAxisId="right" type="monotone" dataKey="margin" name="Margin %" stroke="#ffc658" />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default WhatIfScenario; 