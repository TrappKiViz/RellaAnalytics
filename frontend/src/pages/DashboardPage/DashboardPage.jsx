import React, { useState, useEffect, useMemo, useCallback } from 'react';
import DatePicker from "react-datepicker"; // Import date picker
import "react-datepicker/dist/react-datepicker.css"; // Import date picker styles
import './DashboardPage.css';
import KPI_Card from '../../components/KPI_Card/KPI_Card';
import SalesForecastChart from '../../components/SalesForecastChart/SalesForecastChart'; // Import Forecast Chart
import CategorySalesPieChart from '../../components/CategorySalesPieChart/CategorySalesPieChart';
import TopItemsTable from '../../components/TopItemsTable/TopItemsTable';
// Remove generic SummaryWidget import
// import SummaryWidget from '../../components/SummaryWidget/SummaryWidget'; 
// Import new AISummaryCard
import AISummaryCard from '../../components/AISummaryCard/AISummaryCard'; 
// import AssociationRulesWidget from '../../components/AssociationRulesWidget/AssociationRulesWidget'; // Remove Rules Widget import
import {
  // getSalesSummary, // Keep if needed, but KPIs endpoint is more comprehensive now
  getLocations,
  getProducts,
  getServices,
  getKPIs,
  getSalesByCategory,
  getSalesForecast,
  getCustomerLocations,
  getProfitByCategory
} from '../../services/api';
// import CustomerDensityMap from '../../components/CustomerDensityMap/CustomerDensityMap'; // <-- Remove Map import

const DashboardPage = () => {
  // Data states
  const [kpiData, setKpiData] = useState({}); // Use fetched KPIs
  const [forecastData, setForecastData] = useState({ historical: [], forecast: [], note: '' }); // State for forecast
  const [categorySalesValueData, setCategorySalesValueData] = useState(null); 
  const [categoryGrowthData, setCategoryGrowthData] = useState(null); // Example: Placeholder
  const [categoryCountData, setCategoryCountData] = useState(null); // Example: Placeholder
  const [categoryProfitData, setCategoryProfitData] = useState(null); // State for profit data
  const [locations, setLocations] = useState([]);
  const [summaryText, setSummaryText] = useState(''); // State for summary text
  // const [customerCoords, setCustomerCoords] = useState([]); // <-- Remove Customer Coords state

  // Filter states
  const [selectedLocation, setSelectedLocation] = useState('all'); // 'all' or location_id
  const [startDate, setStartDate] = useState(new Date("2024-01-01")); // Default start (adjust as needed)
  const [endDate, setEndDate] = useState(new Date("2024-03-31"));     // Default end (adjust as needed)

  // Loading and error states
  const [isLoading, setIsLoading] = useState(true); // General loading for KPIs/Charts
  const [error, setError] = useState(null);
  const [forecastError, setForecastError] = useState(null); // Specific error state for forecast

  // State for Pie Chart Dropdown
  const [pieChartMetric, setPieChartMetric] = useState('value'); // 'value', 'growth', 'count', 'profit'

  // --- Helper function to generate summary --- 
  const generateSummary = (kpis, categoryData) => {
    if (!kpis || Object.keys(kpis).length === 0) {
      return 'Waiting for data...';
    }
    
    let summary = `Overall Performance Summary:
`;
    
    // Sales
    summary += `- Total net sales reached ${kpis.total_net_sales?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}.
`;
    summary += `- The average transaction value was ${kpis.avg_transaction_value?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}.
`;
    
    // Top Performers
    if (kpis.top_selling_product && kpis.top_selling_product !== 'N/A') {
      summary += `- The top selling product was ${kpis.top_selling_product} (Sales: ${kpis.top_selling_product_value?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}).
`;
    }
    if (kpis.top_selling_service && kpis.top_selling_service !== 'N/A') {
      summary += `- The top selling service was ${kpis.top_selling_service} (Sales: ${kpis.top_selling_service_value?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}).
`;
    }

    // Category Breakdown
    if (categoryData && categoryData.length > 0) {
      const sortedCategories = [...categoryData].sort((a, b) => b.value - a.value);
      if (sortedCategories[0]?.value > 0) {
        summary += `- ${sortedCategories[0].name} was the highest contributing category.
`;
      }
      // Could add more detail here, e.g., lowest category or distribution
    }
    
    // Customer/Booking KPIs
    summary += `- ${kpis.new_customers_qtd || 0} new customers were acquired.
`;
    summary += `- The booking conversion rate was ${((kpis.booking_conversion_rate || 0) * 100).toFixed(1)}%.
`;
    
    summary += `
Note: This is an illustrative summary based on available data.`
    
    return summary;
  };

  // Fetch Locations (for filter ONLY)
  const loadLocationFilterData = useCallback(async () => {
    // setIsLoadingMapData(true); // <-- Remove
    setError(null); // Clear general error
    try {
      // Fetch only locations for the filter
      const locationsData = await getLocations();
      setLocations(locationsData); // For filter dropdown
    } catch (err) {
      console.error("Error loading location filter data:", err);
      setError("Failed to load location data for filter."); 
      setLocations([]); 
    } finally {
      // setIsLoadingMapData(false); // <-- Remove
    }
  }, []);

  // Function to trigger a reload of all dashboard data
  const refreshDashboardData = () => {
    // Simply re-running the effect dependencies will trigger a reload
    // To ensure it always runs, we could temporarily change a dummy state value,
    // but changing the dates slightly might be simpler if acceptable.
    // Or, more robustly, extract loadDashboardData and call it directly.
    loadDashboardData(); // Call the existing data loading function
  }

  // Fetch main dashboard data (KPIs, charts)
  const loadDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setForecastError(null);

    const filters = {};
    if (selectedLocation !== 'all') {
      filters.location_id = selectedLocation;
    }
    if (startDate) {
      filters.start_date = startDate.toISOString().split('T')[0];
    }
    if (endDate) {
      filters.end_date = endDate.toISOString().split('T')[0];
    }

    try {
      const [kpiResult, categorySalesResult, categoryProfitResult] = await Promise.all([
        getKPIs(filters),
        getSalesByCategory(filters),
        getProfitByCategory(filters)
      ]);

      let forecastResult = { historical: [], forecast: [], note: '' };
      try {
           forecastResult = await getSalesForecast(filters);
      } catch (forecastErr) {
           console.error("Error loading forecast data:", forecastErr);
           setForecastError(forecastErr.message || "Failed to load forecast data.");
           setForecastData({ historical: [], forecast: [], note: '' });
      }

      setKpiData(kpiResult);
      setCategorySalesValueData(categorySalesResult); 
      setCategoryProfitData(categoryProfitResult);
      setForecastData(forecastResult);
      
      // --- MOCK DATA FOR OTHER PIE METRICS (REMOVE LATER) ---
      const generateMockData = (baseData, metricKey, multiplier = 1, isFloat = false) => {
          if (!baseData) return null;
          return baseData.map(item => {
              const randomValue = Math.max(0.1, (Math.random() - 0.4) * multiplier);
              return {
                 ...item,
                 // Store as number
                 [metricKey]: isFloat ? parseFloat(randomValue.toFixed(2)) : parseInt(randomValue.toFixed(0)) 
              };
          });
      };
      // Store growth as float number
      setCategoryGrowthData(generateMockData(categorySalesResult, 'growth', 0.1, true)); 
      // Store count as integer number
      setCategoryCountData(generateMockData(categorySalesResult, 'count', 50, false)); 
      // -- END MOCK DATA ---

      const summary = generateSummary(kpiResult, categorySalesResult);
      setSummaryText(summary);

    } catch (err) {
      console.error("Error loading primary dashboard data:", err);
      setError(err.message);
      setForecastData({ historical: [], forecast: [], note: '' });
    } finally {
      setIsLoading(false);
    }
  }, [selectedLocation, startDate, endDate]);

  // Initial load
  useEffect(() => {
    loadLocationFilterData(); // Fetch location filter data
    loadDashboardData(); // Fetch main dashboard data
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadLocationFilterData, loadDashboardData]); // Adjust dependencies

  // Combine filters for passing down
  const currentFilters = useMemo(() => ({
    location_id: selectedLocation !== 'all' ? selectedLocation : undefined,
    start_date: startDate ? startDate.toISOString().split('T')[0] : undefined,
    end_date: endDate ? endDate.toISOString().split('T')[0] : undefined,
  }), [selectedLocation, startDate, endDate]);

  const handleLocationChange = (event) => {
    setSelectedLocation(event.target.value);
  };

  // Derive top items from KPI data (if available)
  const topProductsData = kpiData.top_selling_product && kpiData.top_selling_product !== "N/A" 
    ? [{ name: kpiData.top_selling_product, value: kpiData.top_selling_product_value }]
    : [];
  const topServicesData = kpiData.top_selling_service && kpiData.top_selling_service !== "N/A"
    ? [{ name: kpiData.top_selling_service, value: kpiData.top_selling_service_value }]
    : [];

  // Filter category data based on the selected metric for Pie Chart
  const pieChartData = useMemo(() => {
      let data = null;
      if (pieChartMetric === 'value') data = categorySalesValueData;
      else if (pieChartMetric === 'profit') data = categoryProfitData;
      else if (pieChartMetric === 'growth') data = categoryGrowthData;
      else if (pieChartMetric === 'count') data = categoryCountData;
      // Add other cases for future metrics

      // Filter out zero/null values for the selected metric
      return data ? data.filter(item => item && parseFloat(item[pieChartMetric]) > 0) : [];
  }, [pieChartMetric, categorySalesValueData, categoryProfitData, categoryGrowthData, categoryCountData]);

  const handlePieMetricChange = (event) => {
      setPieChartMetric(event.target.value);
  };

  return (
    <div className="dashboard-page">
      <h2>Dashboard Overview</h2>

      {/* --- Filter Section --- */}
      <div className="filter-container">
        <div className="filter-group">
            <label htmlFor="location-filter">Location:</label>
            <select id="location-filter" onChange={handleLocationChange} value={selectedLocation} >
                <option value="all">All Locations</option>
                {locations.map(loc => (
                    <option key={loc.location_id} value={loc.location_id}>{loc.name}</option>
                ))}
            </select>
        </div>
        <div className="filter-group">
            <label htmlFor="date-range-filter">Date Range:</label>
            <div className="date-picker-group">
              <DatePicker
                selected={startDate}
                onChange={(date) => setStartDate(date)}
                selectsStart
                startDate={startDate}
                endDate={endDate}
                dateFormat="yyyy-MM-dd"
                placeholderText="Start Date"
                className="date-picker-input"
              />
              <span className="date-separator">to</span>
              <DatePicker
                selected={endDate}
                onChange={(date) => setEndDate(date)}
                selectsEnd
                startDate={startDate}
                endDate={endDate}
                minDate={startDate} // Prevent end date before start date
                dateFormat="yyyy-MM-dd"
                placeholderText="End Date"
                className="date-picker-input"
              />
            </div>
        </div>
      </div>
      {/* --- End Filter Section --- */}

      {isLoading && <p>Loading dashboard data...</p>}
      {error && !isLoading && <p style={{ color: 'red' }}>Error loading dashboard: {error}</p>}

      {!isLoading && !error && (
        <div className="dashboard-content-grid">
          <div className="grid-kpis">
            <div className="kpi-container">
              <KPI_Card title="Total Net Sales" value={kpiData.total_net_sales?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} tooltip={kpiData.calculation_note} />
              <KPI_Card title="Avg. Transaction Value" value={kpiData.avg_transaction_value?.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} />
              <KPI_Card title="New Customers (QTD)" value={kpiData.new_customers_qtd} />
              <KPI_Card title="Booking Conversion" value={`${((kpiData.booking_conversion_rate || 0) * 100).toFixed(1)}%`} />
            </div>
          </div>

          <div className="grid-chart-trend">
             {forecastError ? (
                 <div className="chart-container"><p style={{ color: 'red' }}>Forecast Error: {forecastError}</p></div>
             ) : (
                 <SalesForecastChart 
                     historicalData={forecastData.historical} 
                     forecastData={forecastData.forecast} 
                     note={forecastData.note}
                 />
             )}
          </div>
          
          <div className="grid-chart-pie">
            {/* Add Dropdown for Pie Chart Metric */}
            <div className="chart-header">
              <select value={pieChartMetric} onChange={handlePieMetricChange} className="chart-dropdown">
                <option value="value">Sales by Category</option>
                <option value="profit">Profit by Category</option>
                <option value="growth">Growth Rate by Category (Mock)</option>
                <option value="count">Transaction Count by Category (Mock)</option>
                {/* Add more options later */}
              </select>
            </div>
            {/* Pass selected metric and corresponding data */}
            <CategorySalesPieChart data={pieChartData} dataKey={pieChartMetric} />
          </div>

          <div className="grid-table-products">
            <TopItemsTable title="Top Product (by Sales)" items={topProductsData} valueKey="value" valueLabel="Total Sales" isCurrency={true} />
          </div>

          <div className="grid-table-services">
            <TopItemsTable title="Top Service (by Sales)" items={topServicesData} valueKey="value" valueLabel="Total Sales" isCurrency={true} />
          </div>
          
          <div className="grid-summary">
             {/* Replace SummaryWidget with AISummaryCard */}
             <AISummaryCard title="AI Analysis Summary" summary={summaryText} isLoading={isLoading} />
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage; 