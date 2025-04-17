import React, { useState, useMemo } from 'react';
import { Map } from 'react-map-gl';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import 'mapbox-gl/dist/mapbox-gl.css'; // Import Mapbox CSS

// Your Mapbox API token
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoidHJhcGtydml6IiwiYSI6ImNtOGRxYno0bjAwdGIyam9jYmIwcjl6bTgifQ.ashp0olihLVy-ve2j_IHlw';

// Initial view state for the map
const INITIAL_VIEW_STATE = {
    longitude: -122.1, // Centered roughly between Napa and Vacaville
    latitude: 38.3,
    zoom: 9,
    pitch: 0,
    bearing: 0
};

// Simple linear scale function
const scaleRadius = (value, minVal, maxVal, minRadius, maxRadius) => {
    if (maxVal <= minVal) return minRadius; // Avoid division by zero
    const proportion = (value - minVal) / (maxVal - minVal);
    return minRadius + proportion * (maxRadius - minRadius);
};

const LocationMap = ({ locations }) => {
    const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
    const [tooltip, setTooltip] = useState(null); // Keep tooltip state

    // Calculate min/max sales for scaling radius
    const { minSales, maxSales } = useMemo(() => {
        if (!locations || locations.length === 0) {
            return { minSales: 0, maxSales: 0 };
        }
        // Use sqrt for scaling range calculation as well
        const sales = locations.map(l => Math.sqrt(l.total_sales || 0)); 
        return { minSales: Math.min(...sales), maxSales: Math.max(...sales) };
    }, [locations]);

    // Define deck.gl layers
    const layers = useMemo(() => [
        new ScatterplotLayer({
            id: 'location-scatter',
            data: locations,
            getPosition: d => [d.longitude, d.latitude],
            // Scale radius based on SQRT of total_sales
            getRadius: d => scaleRadius(Math.sqrt(d.total_sales || 0), minSales, maxSales, 1000, 4000), // Adjusted range slightly (1km to 4km)
            radiusUnits: 'meters', // Ensure radius is in meters
            getFillColor: [255, 140, 0, 180], // Orange, slightly transparent
            pickable: true,
            onHover: info => setTooltip(info),
        })
    ], [locations, minSales, maxSales]); // Recalculate layers if locations or scale changes

    // Tooltip content including sales
    const getTooltipContent = ({ object }) => {
        if (!object) return null;
        const formattedSales = (object.total_sales || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
        return `${object.name}\n${object.address}\nTotal Sales: ${formattedSales}`;
    };

    return (
        <DeckGL
            layers={layers}
            initialViewState={viewState}
            controller={true}
            onViewStateChange={e => setViewState(e.viewState)}
            getTooltip={getTooltipContent} // Use updated tooltip function
        >
            <Map
                mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
                mapStyle="mapbox://styles/mapbox/light-v11"
            />
            {/* Basic tooltip display - Will use DeckGL's default tooltip handling now */}
            {/* Remove the manual tooltip div */}
        </DeckGL>
    );
};

export default LocationMap;
