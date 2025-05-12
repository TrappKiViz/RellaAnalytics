import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout'; // Assuming Layout component exists
import { Card, Col, Row, Spin, Alert, Typography } from 'antd'; // Example using Ant Design
// TODO: Replace with actual API service functions
// import { fetchKpis, fetchProfitByCategory } from '../services/api';

const { Title } = Typography;

// Helper function to construct query parameters
const buildQueryString = (params) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      query.append(key, value);
    }
  });
  return query.toString();
};

// TODO: Move API base URL to config or context
const API_BASE_URL = 'http://localhost:5001/api/v1'; // Adjust if needed

function ProfitabilityAnalyticsPage() {
  const [kpiData, setKpiData] = useState(null);
  const [profitByCategory, setProfitByCategory] = useState([]);
  const [loadingKpis, setLoadingKpis] = useState(true);
  const [loadingProfitCat, setLoadingProfitCat] = useState(true);
  const [error, setError] = useState(null);

  // TODO: Implement date range and location filters similar to Dashboard
  // For now, use fixed filters for testing
  const [filters, setFilters] = useState({
      location_id: 'all', // Default or from state
      start_date: '2024-01-01', // Default or from state
      end_date: '2024-03-31', // Default or from state
  });

  useEffect(() => {
    const loadData = async () => {
      setLoadingKpis(true);
      setLoadingProfitCat(true);
      setError(null);
      // Keep previous data while loading?
      // setKpiData(null);
      // setProfitByCategory([]);

      const kpiQueryString = buildQueryString(filters);
      const profitCatQueryString = buildQueryString(filters);

      try {
        // Fetch in parallel
        const [kpiResponse, profitCatResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/kpis?${kpiQueryString}`, {
             method: 'GET',
             headers: {
               // Add necessary headers, e.g., Authorization if using tokens
               // 'Authorization': `Bearer ${token}`,
               'Accept': 'application/json',
             },
             credentials: 'include', // Include cookies for session auth
           }),
          fetch(`${API_BASE_URL}/profit/by_category?${profitCatQueryString}`, {
             method: 'GET',
             headers: {
                 // Add necessary headers
                 'Accept': 'application/json',
             },
             credentials: 'include', // Include cookies for session auth
           }),
        ]);

        // --- Handle KPI Response ---
        if (!kpiResponse.ok) {
            throw new Error(`KPI API Error: ${kpiResponse.status} ${kpiResponse.statusText}`);
        }
        const kpiJson = await kpiResponse.json();
        if (kpiJson && kpiJson.kpis) { // Check structure
             setKpiData(kpiJson.kpis); // Store the nested kpis object
        } else {
             console.warn("Received unexpected KPI data structure:", kpiJson);
             setKpiData({ profitability_by_item: {}, summary: {} }); // Set empty structure
        }
        setLoadingKpis(false);

        // --- Handle Profit By Category Response ---
        if (!profitCatResponse.ok) {
             throw new Error(`Profit Category API Error: ${profitCatResponse.status} ${profitCatResponse.statusText}`);
        }
        const profitCatJson = await profitCatResponse.json();
        if (Array.isArray(profitCatJson)) { // Check structure
             setProfitByCategory(profitCatJson);
        } else {
             console.warn("Received unexpected Profit By Category data structure:", profitCatJson);
             setProfitByCategory([]); // Set empty array
        }
        setLoadingProfitCat(false);

      } catch (err) {
        console.error("Error fetching profitability data:", err);
        setError(`Failed to load profitability data: ${err.message}`);
        setLoadingKpis(false);
        setLoadingProfitCat(false);
      }
    };

    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]); // Use the filters state object directly

  // --- Prepare data for table --- 
  const profitabilityArray = kpiData?.profitability_by_item
    ? Object.entries(kpiData.profitability_by_item).map(([id, data]) => ({ id, ...data }))
    : [];

  // TODO: Add sorting state and logic for the table
  const sortedProfitability = [...profitabilityArray].sort((a, b) => b.profit - a.profit); // Default sort

  return (
    <Layout>
      <Title level={2}>Profitability Analytics</Title>
      {/* TODO: Add Date Range Picker and Location Selector Components */}
      
      {error && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 16 }} />}

      <Row gutter={[16, 16]}>
        {/* Section 1: Profit by Category Chart */}  
        <Col xs={24} lg={12}>
          <Card title="Profit by Category">
            {loadingProfitCat ? (
              <Spin />
            ) : (
              <div>
                {/* TODO: Implement a Pie Chart or Bar Chart here using profitByCategory data */}  
                <p>Chart Placeholder for Profit by Category</p>
                <pre>{JSON.stringify(profitByCategory, null, 2)}</pre>
                 <Alert 
                    type="info" 
                    message="Note: Profit by category uses estimated costs based on mock data defined in the backend." 
                    style={{ marginTop: '10px'}} 
                    showIcon
                 />
              </div>
            )}
          </Card>
        </Col>

        {/* Section 2: Detailed Profitability Table */}  
        <Col xs={24} lg={24}> {/* Full width for table */} 
          <Card title="Detailed Profitability by Item">
            {loadingKpis ? (
              <Spin />
            ) : (
              <div>
                 {/* TODO: Implement a sortable Ant Design Table here using sortedProfitability data */}
                 <p>Table Placeholder for Detailed Profitability</p>
                 <pre>{JSON.stringify(sortedProfitability.slice(0, 10), null, 2)}</pre> {/* Show first 10 items */} 
                 <Alert 
                    type="info" 
                    message={kpiData?.summary?.limitations || "Cost limitations note unavailable."}
                    style={{ marginTop: '10px'}} 
                    showIcon
                 />
              </div>
            )}
          </Card>
        </Col>

      </Row>
    </Layout>
  );
}

export default ProfitabilityAnalyticsPage; 