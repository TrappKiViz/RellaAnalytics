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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { formatCurrency, formatPercentage } from './common/ProfitCard';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function DiscountImpact() {
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

  if (!kpiData?.discounts || kpiData.discounts.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Data</AlertTitle>
        No discount data available for the selected period.
      </Alert>
    );
  }

  // Sort discounts by total amount
  const sortedDiscounts = [...kpiData.discounts].sort((a, b) => b.total_amount - a.total_amount);

  // Calculate total discount amount
  const totalDiscountAmount = sortedDiscounts.reduce((sum, d) => sum + d.total_amount, 0);

  // Prepare data for pie chart
  const pieChartData = sortedDiscounts.map(discount => ({
    name: discount.name,
    value: discount.total_amount,
  }));

  // Prepare data for bar chart
  const barChartData = sortedDiscounts.map(discount => ({
    name: discount.name,
    amount: discount.total_amount,
    impact: Math.abs(discount.profit_impact),
    usage: discount.usage_count,
  }));

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Discount Analysis
      </Typography>
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Total Discounts
              </Typography>
              <Typography variant="h4" color="error">
                {formatCurrency(totalDiscountAmount)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total discount amount across all items
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Most Used Discount
              </Typography>
              <Typography variant="h6">
                {sortedDiscounts[0]?.name || 'N/A'}
              </Typography>
              <Typography variant="body1" color="error">
                {formatCurrency(sortedDiscounts[0]?.total_amount || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Used {sortedDiscounts[0]?.usage_count || 0} times
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Total Profit Impact
              </Typography>
              <Typography variant="h4" color="error">
                {formatCurrency(
                  sortedDiscounts.reduce((sum, d) => sum + Math.abs(d.profit_impact), 0)
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Estimated impact on profits
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Discount Distribution
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Discount Impact Analysis
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={formatCurrency} />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Legend />
                    <Bar dataKey="amount" name="Discount Amount" fill="#8884d8" />
                    <Bar dataKey="impact" name="Profit Impact" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Detailed Discount Analysis
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Discount Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Usage Count</TableCell>
                      <TableCell align="right">Total Amount</TableCell>
                      <TableCell align="right">Average Discount</TableCell>
                      <TableCell align="right">Profit Impact</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedDiscounts.map((discount) => (
                      <TableRow key={discount.name}>
                        <TableCell>{discount.name}</TableCell>
                        <TableCell>{discount.type}</TableCell>
                        <TableCell align="right">{discount.usage_count}</TableCell>
                        <TableCell align="right">{formatCurrency(discount.total_amount)}</TableCell>
                        <TableCell align="right">{formatCurrency(discount.average_discount)}</TableCell>
                        <TableCell align="right">{formatCurrency(Math.abs(discount.profit_impact))}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default DiscountImpact; 