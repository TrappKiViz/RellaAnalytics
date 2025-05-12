import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ProfitOverview from './ProfitOverview';
import ProductProfitability from './ProductProfitability';
import ServiceProfitability from './ServiceProfitability';
import DiscountImpact from './DiscountImpact';
import MarginTrends from './MarginTrends';
import useApiClient from '../../hooks/useApiClient';

// Placeholder for a potential Date Range Picker component
import DateRangePicker from './common/DateRangePicker';

// Styled components
const StyledTabs = styled(Tabs)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  marginBottom: theme.spacing(3),
  '& .MuiTabs-indicator': {
    backgroundColor: theme.palette.primary.main,
  },
}));

const StyledTab = styled(Tab)(({ theme }) => ({
  textTransform: 'none',
  fontWeight: theme.typography.fontWeightMedium,
  fontSize: theme.typography.pxToRem(15),
  marginRight: theme.spacing(1),
  '&.Mui-selected': {
    color: theme.palette.primary.main,
  },
  '&.Mui-focusVisible': {
    backgroundColor: theme.palette.action.selected,
  },
}));

const Header = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: theme.spacing(3),
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    alignItems: 'stretch',
    gap: theme.spacing(2),
  },
}));

// Define tab paths and their corresponding indices
const TAB_PATHS = {
  'overview': 0,
  'products': 1,
  'services': 2,
  'discounts': 3,
};

const TAB_INDICES = {
  0: 'overview',
  1: 'products',
  2: 'services',
  3: 'discounts',
};

function ProfitAnalyticsLayout() {
  console.log("ProfitAnalyticsLayout mounted");
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('30');

  // Get current tab from URL path
  let currentPath = location.pathname.split('/').pop() || 'overview';
  if (currentPath === 'profitability') currentPath = 'overview';
  const currentTabValue = TAB_PATHS[currentPath] ?? 0; // Default to overview (0) if path not found

  const { get } = useApiClient();
  const [kpiData, setKpiData] = useState(null);

  useEffect(() => {
    const fetchKpis = async () => {
      setLoading(true);
      setError(null);
      try {
        // Calculate date range based on selected days
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - parseInt(dateRange));

        // Pass dateRange as query params
        const params = {
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0]
        };

        const response = await get('/api/v1/kpis', params);

        if (response) {
          setKpiData(response);  // Use response directly since it's not wrapped in a kpis object
          console.log("ProfitAnalyticsLayout kpiData", response);
        } else {
          console.warn("[ProfitAnalyticsLayout] KPI data received in unexpected format:", response);
          setKpiData(null);
          setError('Invalid data format received from server');
        }
      } catch (err) {
        console.error("[ProfitAnalyticsLayout] Error caught within fetchKpis try/catch block:", err);
        setKpiData(null);
        setError(err.message || 'Failed to fetch KPI data');
      } finally {
        setLoading(false);
      }
    };

    fetchKpis();
  }, [get, setError, dateRange]);

  const handleTabChange = (event, newValue) => {
    const path = TAB_INDICES[newValue];
    if (path) {
      navigate(`/profitability/${path}`);
    }
  };

  const handleDateRangeChange = (event) => {
    setDateRange(event.target.value);
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Header>
        <Typography variant="h4" component="h1" color="text.primary" fontWeight="600">
          Profitability Analytics
        </Typography>

        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="date-range-label">Date Range</InputLabel>
          <Select
            labelId="date-range-label"
            value={dateRange}
            label="Date Range"
            onChange={handleDateRangeChange}
          >
            <MenuItem value="7">Last 7 Days</MenuItem>
            <MenuItem value="30">Last 30 Days</MenuItem>
            <MenuItem value="90">Last 90 Days</MenuItem>
            <MenuItem value="180">Last 180 Days</MenuItem>
            <MenuItem value="365">Last Year</MenuItem>
          </Select>
        </FormControl>
      </Header>

      <Paper sx={{ mb: 3 }}>
        <StyledTabs
          value={currentTabValue}
          onChange={handleTabChange}
          aria-label="analytics navigation tabs"
        >
          <StyledTab label="Overview" value={0} />
          <StyledTab label="Product Profitability" value={1} />
          <StyledTab label="Service Profitability" value={2} />
          {/* <StyledTab label="Margin Trends" value={3} /> */}
          <StyledTab label="Discount Impact" value={3} />
        </StyledTabs>
      </Paper>

      <Box sx={{ position: 'relative', minHeight: 400 }}>
        {loading ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 400,
            }}
          >
            <CircularProgress sx={{ mb: 2 }} />
            <Typography>Loading analytics data...</Typography>
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 3 }}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        ) : (
          <Outlet context={{ loading, error, kpiData, dateRange }} />
        )}
      </Box>
    </Box>
  );
}

export default ProfitAnalyticsLayout; 