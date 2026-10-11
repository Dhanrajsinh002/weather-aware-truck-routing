import { AddLayerObject } from 'maplibre-gl';
import { RISK_COLORS } from '../../lib/risk';

export const ROUTE_CASING_LAYER_ID = 'route-segments-casing';
export const ROUTE_SEGMENTS_LAYER_ID = 'route-segments';
export const CHECKPOINTS_HALO_LAYER_ID = 'checkpoints-halo';
export const CHECKPOINTS_LAYER_ID = 'checkpoints-circles';
export const HEATMAP_LAYER_ID = 'corridor-heatmap';
export const HEATMAP_POINTS_LAYER_ID = 'corridor-heatmap-points';

export const routeCasingLayer: AddLayerObject = {
  id: ROUTE_CASING_LAYER_ID,
  type: 'line',
  source: 'routes-source',
  layout: {
    'line-join': 'round',
    'line-cap': 'round',
  },
  paint: {
    'line-color': '#0f172a',
    'line-width': ['case', ['get', 'isSelected'], 8, 4.5],
    'line-opacity': ['case', ['get', 'isSelected'], 0.8, 0.25],
  },
};

export const routeSegmentsLayer: AddLayerObject = {
  id: ROUTE_SEGMENTS_LAYER_ID,
  type: 'line',
  source: 'routes-source',
  layout: {
    'line-join': 'round',
    'line-cap': 'round',
  },
  paint: {
    'line-color': [
      'match',
      ['get', 'level'],
      'LOW', RISK_COLORS.LOW,
      'MODERATE', RISK_COLORS.MODERATE,
      'HIGH', RISK_COLORS.HIGH,
      'SEVERE', RISK_COLORS.SEVERE,
      'NO_TRAVEL', RISK_COLORS.NO_TRAVEL,
      '#64748b',
    ],
    'line-width': ['case', ['get', 'isSelected'], 5, 2.5],
    'line-opacity': ['case', ['get', 'isSelected'], 1.0, 0.45],
  },
};

export const checkpointsHaloLayer: AddLayerObject = {
  id: CHECKPOINTS_HALO_LAYER_ID,
  type: 'circle',
  source: 'checkpoints-source',
  paint: {
    'circle-color': [
      'match',
      ['get', 'level'],
      'LOW', RISK_COLORS.LOW,
      'MODERATE', RISK_COLORS.MODERATE,
      'HIGH', RISK_COLORS.HIGH,
      'SEVERE', RISK_COLORS.SEVERE,
      'NO_TRAVEL', RISK_COLORS.NO_TRAVEL,
      '#64748b',
    ],
    'circle-radius': ['case', ['get', 'isHovered'], 14, 0],
    'circle-opacity': 0.4,
  },
};

export const checkpointsCircleLayer: AddLayerObject = {
  id: CHECKPOINTS_LAYER_ID,
  type: 'circle',
  source: 'checkpoints-source',
  paint: {
    'circle-color': [
      'match',
      ['get', 'level'],
      'LOW', RISK_COLORS.LOW,
      'MODERATE', RISK_COLORS.MODERATE,
      'HIGH', RISK_COLORS.HIGH,
      'SEVERE', RISK_COLORS.SEVERE,
      'NO_TRAVEL', RISK_COLORS.NO_TRAVEL,
      '#64748b',
    ],
    'circle-radius': ['case', ['get', 'isHovered'], 8.5, 5.5],
    'circle-stroke-width': ['case', ['get', 'isHovered'], 2.5, 1.5],
    'circle-stroke-color': '#ffffff',
  },
};

export const heatmapLayer: AddLayerObject = {
  id: HEATMAP_LAYER_ID,
  type: 'heatmap',
  source: 'heatmap-source',
  maxzoom: 12,
  paint: {
    // Increase the heatmap weight based on risk level
    'heatmap-weight': ['get', 'weight'],
    // Heatmap intensity transition
    'heatmap-intensity': [
      'interpolate',
      ['linear'],
      ['zoom'],
      0, 0.8,
      5, 1.5,
      9, 3.0,
    ],
    // Color ramp: transparent -> Green -> Yellow -> Orange -> Red -> Dark Red
    'heatmap-color': [
      'interpolate',
      ['linear'],
      ['heatmap-density'],
      0, 'rgba(0,0,0,0)',
      0.15, 'rgba(16, 185, 129, 0.4)', // Low (green)
      0.35, '#10b981', // Low solid
      0.55, '#eab308', // Moderate (yellow)
      0.75, '#f97316', // High (orange)
      0.90, '#ef4444', // Severe (red)
      1.0, '#881337', // No Travel (dark red)
    ],
    // Radius of influence per point
    'heatmap-radius': [
      'interpolate',
      ['linear'],
      ['zoom'],
      0, 15,
      4, 30,
      7, 55,
      10, 80,
    ],
    'heatmap-opacity': 0.72,
  },
};

export const heatmapPointsLayer: AddLayerObject = {
  id: HEATMAP_POINTS_LAYER_ID,
  type: 'circle',
  source: 'heatmap-source',
  minzoom: 7,
  paint: {
    'circle-radius': 4.5,
    'circle-color': [
      'match',
      ['get', 'level'],
      0, RISK_COLORS.LOW,
      1, RISK_COLORS.MODERATE,
      2, RISK_COLORS.HIGH,
      3, RISK_COLORS.SEVERE,
      4, RISK_COLORS.NO_TRAVEL,
      '#64748b',
    ],
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': [
      'interpolate',
      ['linear'],
      ['zoom'],
      7, 0,
      8.5, 0.85,
    ],
  },
};
