import React, { useState, useMemo, useEffect } from 'react';
import { Map, NavigationControl } from 'react-map-gl';
import { AmbientLight, PointLight, LightingEffect, _SunLight as SunLight } from '@deck.gl/core';
import { HexagonLayer } from '@deck.gl/aggregation-layers';
import { ScatterplotLayer } from '@deck.gl/layers';
import { GeoJsonLayer } from '@deck.gl/layers';
import DeckGL from '@deck.gl/react';
import { scaleThreshold } from 'd3-scale';
import 'mapbox-gl/dist/mapbox-gl.css';

// Your Mapbox API token
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoidHJhcGtydml6IiwiYSI6ImNtOGRxYno0bjAwdGIyam9jYmIwcjl6bTgifQ.ashp0olihLVy-ve2j_IHlw';

// --- View States --- 
const SCATTER_INITIAL_VIEW_STATE = { longitude: -122.1, latitude: 38.3, zoom: 9, pitch: 0, bearing: 0 };
const GEOJSON_INITIAL_VIEW_STATE = { longitude: -122.1, latitude: 38.3, zoom: 9.5, maxZoom: 16, pitch: 30, bearing: 0 };
const HEXAGON_INITIAL_VIEW_STATE = { longitude: -122.1, latitude: 38.3, zoom: 9, pitch: 30, bearing: 0 };

// --- Map Styles --- 
const MAP_STYLE_LIGHT = 'mapbox://styles/mapbox/light-v11';
const MAP_STYLE_DARK = 'mapbox://styles/mapbox/dark-v11';

// --- Lighting --- 
// Basic lighting for scatter
const scatterAmbientLight = new AmbientLight({ color: [255, 255, 255], intensity: 1.0 });
const scatterPointLight = new PointLight({ color: [255, 255, 255], intensity: 0.8, position: [-122.1, 38.3, 80000] });
const scatterLightingEffect = new LightingEffect({ ambientLight: scatterAmbientLight, pointLight1: scatterPointLight });
// Lighting for GeoJson example
const geojsonAmbientLight = new AmbientLight({ color: [255, 255, 255], intensity: 1.0 });
const geojsonDirLight = new SunLight({ timestamp: Date.UTC(2019, 7, 1, 22), color: [255, 255, 255], intensity: 1.0, _shadow: false });
const geojsonLightingEffect = new LightingEffect({ ambientLight: geojsonAmbientLight, dirLight: geojsonDirLight });
// Restore Hexagon lighting
const hexagonAmbientLight = new AmbientLight({ color: [255, 255, 255], intensity: 1.0 });
const hexagonPointLight = new PointLight({ color: [255, 255, 255], intensity: 0.8, position: [-122.1, 38.3, 80000] });
const hexagonLightingEffect = new LightingEffect({ ambientLight: hexagonAmbientLight, pointLight1: hexagonPointLight });

// --- Layer Specific Constants ---
// GeoJSON
const COLOR_SCALE = scaleThreshold()
  .domain([-0.6, -0.45, -0.3, -0.15, 0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2])
  .range([
    [65, 182, 196], [127, 205, 187], [199, 233, 180], [237, 248, 177],
    [255, 255, 204], [255, 237, 160], [254, 217, 118], [254, 178, 76],
    [253, 141, 60], [252, 78, 42], [227, 26, 28], [189, 0, 38], [128, 0, 38]
  ]);
// Hexagon (Restore)
const colorRange = [
  [1, 152, 189],
  [73, 227, 206],
  [216, 254, 181],
  [254, 237, 177],
  [254, 173, 84],
  [209, 55, 78]
];

// --- Main Map Component --- 
const MapView = ({ data, layerType = 'scatter' }) => {
    
    // Determine initial state, map style, effects based on layer type
    const initialViewState = 
        layerType === 'geojson' ? GEOJSON_INITIAL_VIEW_STATE : 
        layerType === 'hexagon' ? HEXAGON_INITIAL_VIEW_STATE : 
        SCATTER_INITIAL_VIEW_STATE; // Default to scatter
    // Always use light style
    const mapStyle = MAP_STYLE_LIGHT;
    const effects = 
        layerType === 'geojson' ? [geojsonLightingEffect] : 
        layerType === 'hexagon' ? [hexagonLightingEffect] :
        [scatterLightingEffect]; // Default to scatter
    
    // View state management
    const [viewState, setViewState] = useState(initialViewState);
    // Restore effect resetting view state based on layerType
    useEffect(() => {
        setViewState(initialViewState);
    }, [layerType, initialViewState]);

    // Define Layers conditionally
    const layers = useMemo(() => {
        if (layerType === 'scatter') {
            return [
                new ScatterplotLayer({
                    id: 'customer-scatter',
                    data: data,
                    getPosition: d => d,
                    getRadius: 50,
                    radiusUnits: 'pixels',
                    getFillColor: [209, 55, 78, 180],
                    pickable: true,
                })
            ];
        } 
        if (layerType === 'hexagon') {
            return [
                 new HexagonLayer({
                    id: 'customer-hexagon',
                    colorRange,
                    coverage: 0.8, 
                    data: data, 
                    elevationRange: [0, 1000], 
                    elevationScale: data && data.length ? 150 : 0, 
                    extruded: true,
                    getPosition: d => d,
                    pickable: true,
                    radius: 1000, 
                    upperPercentile: 100,
                })
            ];
        }
        if (layerType === 'geojson') {
            return [
                new GeoJsonLayer({
                    id: 'geojson-sales',
                    data: data, // Use the data prop (URL)
                    opacity: 0.8,
                    stroked: false,
                    filled: true,
                    extruded: true,
                    wireframe: true,
                    getElevation: f => Math.sqrt(f.properties.valuePerSqm || 0) * 100, 
                    getFillColor: f => COLOR_SCALE(f.properties.growth || 0),
                    getLineColor: [255, 255, 255],
                    pickable: true,
                })
            ];
        }
        return []; // Should not happen with default
    }, [data, layerType]);

    // Define Tooltip conditionally
    const getTooltip = useMemo(() => {
        if (layerType === 'scatter') {
            return ({ object }) => {
                if (!object) return null;
                const [lng, lat] = object;
                return `Customer Location:\nLon: ${lng.toFixed(6)}\nLat: ${lat.toFixed(6)}`;
            };
        }
         if (layerType === 'hexagon') {
            return ({ object }) => {
                if (!object) return null;
                const lat = object.position[1];
                const lng = object.position[0];
                const count = object.count;
                return `
                    Lat: ${Number.isFinite(lat) ? lat.toFixed(6) : ''}
                    Lon: ${Number.isFinite(lng) ? lng.toFixed(6) : ''}
                    ${count} Customers
                `;
            };
        }
        if (layerType === 'geojson') {
            return ({ object }) => {
                return (
                    object && {
                        html: `\
                            <div><b>Avg Property Value (Simulated Sales)</b></div>
                            <div>Val/Parcel: ${object.properties.valuePerParcel}</div>
                            <div>Val/SqM: ${object.properties.valuePerSqm}</div>
                            <div><b>Growth (Simulated Trend)</b></div>
                            <div>${Math.round(object.properties.growth * 100)}%</div>
                        `
                    }
                );
            };
        }
        return null;
    }, [layerType]);

    // Determine if legend should be shown (only for hexagons)
    const showLegend = layerType === 'hexagon';

    return (
        <div style={{position: 'relative', width: '100%', height: '100%'}}> {/* Ensure relative positioning for overlay */} 
            <DeckGL
                layers={layers}
                effects={effects}
                initialViewState={viewState} // Use initialViewState which changes with layerType
                controller={true}
                onViewStateChange={e => setViewState(e.viewState)} // Allow user control
                getTooltip={getTooltip}
            >
                <Map
                    reuseMaps 
                    mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
                    mapStyle={mapStyle}
                >
                    <NavigationControl position="top-right" /> 
                </Map>
            </DeckGL>

            {/* Simple Legend - Conditionally Render */} 
            {showLegend && (
                <div className="legend-overlay">
                    <div>Customer Density</div>
                    {colorRange.map((color, index) => (
                        <div key={index} className="legend-item">
                            <span 
                                className="legend-color-box" 
                                style={{ backgroundColor: `rgb(${color[0]}, ${color[1]}, ${color[2]})` }}>
                            </span>
                            <span>{index === 0 ? 'Low' : (index === colorRange.length - 1 ? 'High' : '')}</span>
                        </div>
                    ))}
                </div>
            )}
        </div> 
    );
};

export default MapView; 