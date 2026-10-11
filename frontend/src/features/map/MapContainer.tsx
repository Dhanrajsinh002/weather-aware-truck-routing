import React, { useEffect, useRef, useMemo, useCallback } from 'react';
import maplibregl, { Map as MapLibreMap, Popup, LngLatBounds, GeoJSONSource } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useTripContext } from '../../context/TripContext';
import {
  buildRoutesSegmentsGeoJSON,
  buildCheckpointsGeoJSON,
  precomputeHeatmapHourlyCollections,
} from './mapDataHelpers';
import {
  routeCasingLayer,
  routeSegmentsLayer,
  checkpointsHaloLayer,
  checkpointsCircleLayer,
  heatmapLayer,
  heatmapPointsLayer,
  ROUTE_SEGMENTS_LAYER_ID,
  CHECKPOINTS_LAYER_ID,
} from './layers';
import { formatLocalTime } from '../../lib/format';
import { formatRiskLabel, getRiskColor, getRiskBgColor } from '../../lib/risk';
import { Layers, Eye, EyeOff } from 'lucide-react';

import { RiskLevel } from '../../types/api';

const OPEN_FREE_MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty';

interface PopupDisplayProps {
  index: number;
  mile: number;
  level: RiskLevel;
  eta: string;
  wind_mph: number;
  gust_mph: number;
  rain_in_hr: number;
  snow_in_hr: number;
  drivers?: string;
}

export const MapContainer: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<Popup | null>(null);
  const isMapLoadedRef = useRef<boolean>(false);
  const rafIdRef = useRef<number | null>(null);

  const {
    tripData,
    selectedRouteId,
    setSelectedRouteId,
    selectedRoute,
    hoveredCheckpointIndex,
    setHoveredCheckpointIndex,
    popupCheckpoint,
    sliderHour,
    showHeatmap,
    setShowHeatmap,
    showCheckpoints,
    setShowCheckpoints,
  } = useTripContext();

  const setSelectedRouteIdRef = useRef(setSelectedRouteId);
  setSelectedRouteIdRef.current = setSelectedRouteId;
  const setHoveredCheckpointIndexRef = useRef(setHoveredCheckpointIndex);
  setHoveredCheckpointIndexRef.current = setHoveredCheckpointIndex;

  // Precompute 49 hourly heatmap FeatureCollections
  const heatmapHourlyCollections = useMemo(() => {
    if (!tripData || !tripData.heatmap) return [];
    return precomputeHeatmapHourlyCollections(tripData.heatmap);
  }, [tripData]);

  // Helper to render checkpoint popup
  const showCheckpointPopup = useCallback((coords: [number, number], props: PopupDisplayProps) => {
    const map = mapRef.current;
    if (!map) return;

    if (popupRef.current) {
      popupRef.current.remove();
    }

    const riskLevel = props.level;
    const riskColor = getRiskColor(riskLevel);
    const riskBg = getRiskBgColor(riskLevel);
    const formattedEta = formatLocalTime(props.eta);
    const driverText = props.drivers || '';

    const popupHtml = `
      <div class="map-popup-card">
        <div class="popup-header" style="border-left: 4px solid ${riskColor};">
          <div class="popup-title-group">
            <span class="popup-index">Checkpoint #${props.index}</span>
            <span class="popup-mile">Mile ${Number(props.mile).toFixed(1)}</span>
          </div>
          <span class="popup-risk-badge" style="color: ${riskColor}; background: ${riskBg}; border: 1px solid ${riskColor};">
            ${formatRiskLabel(riskLevel)}
          </span>
        </div>
        <div class="popup-body">
          <div class="popup-row">
            <span class="popup-label">Local ETA:</span>
            <span class="popup-val">${formattedEta}</span>
          </div>
          <div class="popup-row">
            <span class="popup-label">Wind:</span>
            <span class="popup-val">${Number(props.wind_mph).toFixed(0)} mph (gusts ${Number(props.gust_mph).toFixed(0)} mph)</span>
          </div>
          <div class="popup-row">
            <span class="popup-label">Precipitation:</span>
            <span class="popup-val">Rain ${Number(props.rain_in_hr).toFixed(2)} in/h · Snow ${Number(props.snow_in_hr).toFixed(1)} in/h</span>
          </div>
          ${
            driverText
              ? `<div class="popup-driver-box">
                  <span class="popup-driver-icon">⚠️</span>
                  <span>${driverText}</span>
                </div>`
              : ''
          }
        </div>
      </div>
    `;

    popupRef.current = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      offset: 12,
      maxWidth: '320px',
      className: 'custom-map-popup',
    })
      .setLngLat(coords)
      .setHTML(popupHtml)
      .addTo(map);
  }, []);

  const showCheckpointPopupRef = useRef(showCheckpointPopup);
  showCheckpointPopupRef.current = showCheckpointPopup;

  // Derived GeoJSON for route segments
  const routesSegmentsGeoJSON = useMemo(() => {
    if (!tripData || !tripData.routes) return { type: 'FeatureCollection' as const, features: [] };
    return buildRoutesSegmentsGeoJSON(tripData.routes, selectedRouteId);
  }, [tripData, selectedRouteId]);

  // Derived GeoJSON for checkpoints
  const checkpointsGeoJSON = useMemo(() => {
    if (!selectedRoute || !selectedRoute.checkpoints) {
      return { type: 'FeatureCollection' as const, features: [] };
    }
    return buildCheckpointsGeoJSON(selectedRoute.checkpoints, hoveredCheckpointIndex);
  }, [selectedRoute, hoveredCheckpointIndex]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: OPEN_FREE_MAP_STYLE,
      center: [-96.0, 40.8], // Central US / Midwest
      zoom: 4.8,
      attributionControl: false, // Customized below
    });

    // Custom attribution control with Open-Meteo & OpenFreeMap
    map.addControl(
      new maplibregl.AttributionControl({
        customAttribution: [
          '<a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap</a>',
          '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a>',
          '<a href="https://open-meteo.com/" target="_blank">Weather data by Open-Meteo (CC BY 4.0)</a>',
        ],
        compact: false,
      }),
      'bottom-right'
    );

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'imperial' }), 'bottom-left');

    map.on('load', () => {
      isMapLoadedRef.current = true;

      // Add Sources
      map.addSource('heatmap-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.addSource('routes-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.addSource('checkpoints-source', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      // Add Layers
      map.addLayer(heatmapLayer);
      map.addLayer(heatmapPointsLayer);
      map.addLayer(routeCasingLayer);
      map.addLayer(routeSegmentsLayer);
      map.addLayer(checkpointsHaloLayer);
      map.addLayer(checkpointsCircleLayer);

      // Route click interaction
      map.on('click', ROUTE_SEGMENTS_LAYER_ID, (e) => {
        if (e.features && e.features[0]) {
          const clickedRouteId = e.features[0].properties?.routeId;
          if (clickedRouteId) {
            setSelectedRouteIdRef.current(clickedRouteId);
          }
        }
      });

      map.on('mouseenter', ROUTE_SEGMENTS_LAYER_ID, () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', ROUTE_SEGMENTS_LAYER_ID, () => {
        map.getCanvas().style.cursor = '';
      });

      // Checkpoint hover & click interactions
      map.on('mouseenter', CHECKPOINTS_LAYER_ID, (e) => {
        map.getCanvas().style.cursor = 'pointer';
        if (e.features && e.features[0]) {
          const index = e.features[0].properties?.index;
          if (typeof index === 'number') {
            setHoveredCheckpointIndexRef.current(index);
          }
        }
      });

      map.on('mouseleave', CHECKPOINTS_LAYER_ID, () => {
        map.getCanvas().style.cursor = '';
        setHoveredCheckpointIndexRef.current(null);
      });

      map.on('click', CHECKPOINTS_LAYER_ID, (e) => {
        if (e.features && e.features[0]) {
          const props = e.features[0].properties;
          const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;
          if (props && coords) {
            showCheckpointPopupRef.current(coords as [number, number], props as unknown as PopupDisplayProps);
          }
        }
      });
    });

    mapRef.current = map;

    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update Routes Source
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    const source = map.getSource('routes-source') as GeoJSONSource | undefined;
    if (source) {
      source.setData(routesSegmentsGeoJSON);
    }
  }, [routesSegmentsGeoJSON]);

  // Update Checkpoints Source
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    const source = map.getSource('checkpoints-source') as GeoJSONSource | undefined;
    if (source) {
      source.setData(checkpointsGeoJSON);
    }
  }, [checkpointsGeoJSON]);

  // Update Heatmap Source based on sliderHour (requestAnimationFrame for ultra-smooth 60fps scrubbing)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
    }

    rafIdRef.current = requestAnimationFrame(() => {
      const source = map.getSource('heatmap-source') as GeoJSONSource | undefined;
      if (source && heatmapHourlyCollections[sliderHour]) {
        source.setData(heatmapHourlyCollections[sliderHour]);
      }
    });

    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, [sliderHour, heatmapHourlyCollections]);

  // Layer Visibility Toggles
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMapLoadedRef.current) return;

    const heatmapVisibility = showHeatmap ? 'visible' : 'none';
    if (map.getLayer(heatmapLayer.id)) {
      map.setLayoutProperty(heatmapLayer.id, 'visibility', heatmapVisibility);
    }
    if (map.getLayer(heatmapPointsLayer.id)) {
      map.setLayoutProperty(heatmapPointsLayer.id, 'visibility', heatmapVisibility);
    }

    const checkpointsVisibility = showCheckpoints ? 'visible' : 'none';
    if (map.getLayer(checkpointsHaloLayer.id)) {
      map.setLayoutProperty(checkpointsHaloLayer.id, 'visibility', checkpointsVisibility);
    }
    if (map.getLayer(checkpointsCircleLayer.id)) {
      map.setLayoutProperty(checkpointsCircleLayer.id, 'visibility', checkpointsVisibility);
    }
  }, [showHeatmap, showCheckpoints]);

  // Fit bounds when tripData or selectedRoute changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !tripData || !tripData.routes || tripData.routes.length === 0) return;

    const bounds = new LngLatBounds();
    let hasCoords = false;

    tripData.routes.forEach((r) => {
      r.geometry.coordinates.forEach((coord) => {
        bounds.extend(coord as [number, number]);
        hasCoords = true;
      });
    });

    if (hasCoords) {
      const fit = () => {
        map.fitBounds(bounds, {
          padding: { top: 60, bottom: 80, left: 60, right: 60 },
          maxZoom: 10,
          duration: 1200,
        });
      };

      if (isMapLoadedRef.current) {
        fit();
      } else {
        map.once('load', fit);
      }
    }
  }, [tripData]);

  // Popup sync from context (e.g. clicking list item)
  useEffect(() => {
    if (!popupCheckpoint) {
      if (popupRef.current) popupRef.current.remove();
      return;
    }

    const coords: [number, number] = [popupCheckpoint.lng, popupCheckpoint.lat];
    showCheckpointPopup(coords, {
      index: popupCheckpoint.index,
      mile: popupCheckpoint.mile,
      level: popupCheckpoint.risk.level,
      eta: popupCheckpoint.eta,
      wind_mph: popupCheckpoint.weather.wind_mph,
      gust_mph: popupCheckpoint.weather.gust_mph ?? popupCheckpoint.weather.wind_mph,
      rain_in_hr: popupCheckpoint.weather.rain_in_hr,
      snow_in_hr: popupCheckpoint.weather.snow_in_hr,
      drivers: popupCheckpoint.risk.drivers.join(', '),
    });

    mapRef.current?.flyTo({
      center: coords,
      zoom: Math.max(mapRef.current.getZoom(), 7.5),
      duration: 600,
    });
  }, [popupCheckpoint, showCheckpointPopup]);

  return (
    <div className="map-wrapper">
      <div ref={mapContainerRef} className="map-element" id="maplibre-container" />

      {/* Floating Layer Controls */}
      <div className="map-layer-toggles">
        <button
          type="button"
          className={`layer-toggle-btn ${showHeatmap ? 'toggle-active' : ''}`}
          onClick={() => setShowHeatmap((prev) => !prev)}
          title="Toggle Corridor Weather Heatmap"
        >
          <Layers size={14} />
          <span>Heatmap</span>
          {showHeatmap ? <Eye size={13} /> : <EyeOff size={13} />}
        </button>

        <button
          type="button"
          className={`layer-toggle-btn ${showCheckpoints ? 'toggle-active' : ''}`}
          onClick={() => setShowCheckpoints((prev) => !prev)}
          title="Toggle Checkpoint Markers"
        >
          <span>Checkpoints</span>
          {showCheckpoints ? <Eye size={13} /> : <EyeOff size={13} />}
        </button>
      </div>

      {/* Map Legend */}
      <div className="map-legend-card">
        <div className="legend-title">Weather Risk Scale</div>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color-dot" style={{ backgroundColor: getRiskColor('LOW') }} />
            <span className="legend-label">Low</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-dot" style={{ backgroundColor: getRiskColor('MODERATE') }} />
            <span className="legend-label">Moderate</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-dot" style={{ backgroundColor: getRiskColor('HIGH') }} />
            <span className="legend-label">High</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-dot" style={{ backgroundColor: getRiskColor('SEVERE') }} />
            <span className="legend-label">Severe</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-dot" style={{ backgroundColor: getRiskColor('NO_TRAVEL') }} />
            <span className="legend-label">No Travel</span>
          </div>
        </div>
      </div>
    </div>
  );
};
