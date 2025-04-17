import React, { useState, useEffect, useCallback } from 'react';
// Import the renamed component
import MapView from '../../components/MapView/MapView.jsx'; 
// Restore API import
import { getCustomerLocations } from '../../services/api'; 
import './MapViewPage.css'; 

// --- Remove Sample Data ---
/*
const sampleCustomerCoords = [
    // ... (sample data lines) ...
];
*/

function MapViewPage() {
    // Initialize with empty array, will be fetched
    const [customerCoords, setCustomerCoords] = useState([]); 
    const [isLoading, setIsLoading] = useState(false); 
    const [error, setError] = useState(null); 
    // Restore selectedLayer state, default to scatter
    const [selectedLayer, setSelectedLayer] = useState('scatter'); 

    // Restore data loading logic
    const loadMapData = useCallback(async () => {
        // Fetch data if scatter or hexagon is selected
        if (selectedLayer === 'scatter' || selectedLayer === 'hexagon') { 
            setIsLoading(true);
            setError(null);
            try {
                const data = await getCustomerLocations();
                setCustomerCoords(data);
            } catch (err) {
                console.error("Error loading customer locations:", err);
                setError(err); 
                setCustomerCoords([]); // Clear data on error
            } finally {
                setIsLoading(false);
            }
        } else if (selectedLayer === 'geojson') {
             // No data fetch needed for static GeoJSON example
             setCustomerCoords([]); // Clear customer data if switching to GeoJSON
             setIsLoading(false);
             setError(null);
        }
        // else: No action needed for other potential future layer types
    }, [selectedLayer]); // Re-fetch when layer changes

    useEffect(() => {
        loadMapData();
    }, [loadMapData]);
    

    // Restore layer change handler
    const handleLayerChange = (event) => {
       setSelectedLayer(event.target.value);
       // Data fetching is handled by useEffect reacting to selectedLayer change
    };

    return (
        <div className="map-view-page">
            <div className="map-container-fullpage"> 
                {/* Restore Layer Selection Dropdown Overlay INSIDE the container */}
                <div className="map-controls-overlay">
                     <label htmlFor="layer-select">View:</label>
                     <select id="layer-select" value={selectedLayer} onChange={handleLayerChange}>
                         {/* Update label to remove (Sample) */}
                         <option value="scatter">Customer Locations</option> 
                         <option value="hexagon">Customer Density (Hexagons)</option> 
                         <option value="geojson">Sales Value Blocks (Demo)</option>
                     </select>
                </div>

                {isLoading && <p>Loading Map Data...</p>}
                {error && <p style={{ color: 'red' }}>Error: {error.message || 'Failed to load map data.'}</p>}
                
                {/* Render MapView, passing layerType and conditional data */}
                {!isLoading && !error && (
                    <MapView 
                        layerType={selectedLayer} 
                        // Pass coords for scatter/hexagon, path for geojson
                        data={selectedLayer === 'geojson' ? '/data/napa-vacaville-blocks.json' : customerCoords}
                    />
                )}
            </div>
        </div>
    );
}

export default MapViewPage; 