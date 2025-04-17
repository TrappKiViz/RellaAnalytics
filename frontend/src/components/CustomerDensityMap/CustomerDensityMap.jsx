import React, { useState, useMemo } from 'react';
import { Map, NavigationControl } from 'react-map-gl';
import { ScatterplotLayer } from '@deck.gl/layers';
import DeckGL from '@deck.gl/react';
import 'mapbox-gl/dist/mapbox-gl.css'; 

// Your Mapbox API token
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoidHJhcGtydml6IiwiYSI6ImNtOGRxYno0bjAwdGIyam9jYmIwcjl6bTgifQ.ashp0olihLVy-ve2j_IHlw';

// --- Initial View State (Keep simple view state) ---
const INITIAL_VIEW_STATE = {
    longitude: -122.1, 
    latitude: 38.3,
    zoom: 9,
    pitch: 0, // Reset pitch
    bearing: 0 // Reset bearing
};

// --- Map Style (Keep light style) ---
const MAP_STYLE = 'mapbox://styles/mapbox/light-v11';

// --- Main Map Component --- 
// Expects customerCoords: [[lon, lat], ...]
const CustomerDensityMap = ({ customerCoords }) => { // Remove unused props
    const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

    // Define the Scatterplot Layer
    const layers = useMemo(() => [
        new ScatterplotLayer({
            id: 'customer-scatter', // New ID
            data: customerCoords, 
            getPosition: d => d, // Data points are [lon, lat]
            
            // Scatterplot layer props
            getRadius: 50, // Radius in pixels (adjust as needed)
            radiusUnits: 'pixels',
            getFillColor: [209, 55, 78, 180], // Use one of the theme colors (e.g., red/pink)
            pickable: true, // Allow hover
        })
    ], [customerCoords]); // Only depends on coordinates now

    // Simple tooltip for scatterplot
    const getTooltip = ({ object }) => {
        if (!object) {
            return null;
        }
        // object is the coordinate pair [lon, lat]
        const [lng, lat] = object;
        return `Customer Location:\nLon: ${lng.toFixed(6)}\nLat: ${lat.toFixed(6)}`;
    };

    return (
        <DeckGL
            layers={layers}
            initialViewState={viewState}
            controller={true}
            onViewStateChange={e => setViewState(e.viewState)}
            getTooltip={getTooltip}
        >
            <Map
                reuseMaps 
                mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
                mapStyle={MAP_STYLE}
            >
                <NavigationControl position="top-right" /> 
            </Map>
        </DeckGL>
    );
};

export default CustomerDensityMap; 