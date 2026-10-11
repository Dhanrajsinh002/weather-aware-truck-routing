import { RouteOption, Checkpoint, HeatmapData, RiskLevel } from '../../types/api';

export interface RouteSegmentFeature {
  type: 'Feature';
  properties: {
    routeId: string;
    isSelected: boolean;
    level: RiskLevel;
    score: number;
    segmentIndex: number;
    label: string;
  };
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  };
}

export function buildRoutesSegmentsGeoJSON(
  routes: RouteOption[],
  selectedRouteId: string | null
): GeoJSON.FeatureCollection<GeoJSON.LineString> {
  const features: GeoJSON.Feature<GeoJSON.LineString>[] = [];

  routes.forEach((route) => {
    const isSelected = route.id === selectedRouteId;
    const coords = route.geometry.coordinates;
    const checkpoints = route.checkpoints;

    if (!coords || coords.length < 2) return;

    if (!checkpoints || checkpoints.length === 0) {
      // Fallback single line if no checkpoints
      features.push({
        type: 'Feature',
        properties: {
          routeId: route.id,
          isSelected,
          level: route.metrics.max_level,
          score: 1,
          segmentIndex: 0,
          label: route.label,
        },
        geometry: {
          type: 'LineString',
          coordinates: coords,
        },
      });
      return;
    }

    // Split route into segments between checkpoint midpoints
    const n = checkpoints.length;
    for (let i = 0; i < n; i++) {
      const chk = checkpoints[i];
      const startFrac = i === 0 ? 0 : (i - 0.5) / (n - 1);
      const endFrac = i === n - 1 ? 1 : (i + 0.5) / (n - 1);

      const startIdx = Math.floor(startFrac * (coords.length - 1));
      const endIdx = Math.min(coords.length - 1, Math.ceil(endFrac * (coords.length - 1)));

      if (endIdx > startIdx) {
        const segCoords = coords.slice(startIdx, endIdx + 1);
        if (segCoords.length >= 2) {
          features.push({
            type: 'Feature',
            properties: {
              routeId: route.id,
              isSelected,
              level: chk.risk.level,
              score: chk.risk.score,
              segmentIndex: i,
              label: route.label,
            },
            geometry: {
              type: 'LineString',
              coordinates: segCoords,
            },
          });
        }
      }
    }
  });

  return {
    type: 'FeatureCollection',
    features,
  };
}

export function buildCheckpointsGeoJSON(
  checkpoints: Checkpoint[],
  hoveredIndex: number | null
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  const features: GeoJSON.Feature<GeoJSON.Point>[] = checkpoints.map((chk) => ({
    type: 'Feature',
    properties: {
      index: chk.index,
      mile: chk.mile,
      eta: chk.eta,
      level: chk.risk.level,
      score: chk.risk.score,
      wind_mph: chk.weather.wind_mph,
      gust_mph: chk.weather.gust_mph ?? chk.weather.wind_mph,
      rain_in_hr: chk.weather.rain_in_hr,
      snow_in_hr: chk.weather.snow_in_hr,
      drivers: chk.risk.drivers.join(', '),
      isHovered: chk.index === hoveredIndex,
    },
    geometry: {
      type: 'Point',
      coordinates: [chk.lng, chk.lat],
    },
  }));

  return {
    type: 'FeatureCollection',
    features,
  };
}

export function precomputeHeatmapHourlyCollections(
  heatmap: HeatmapData
): GeoJSON.FeatureCollection<GeoJSON.Point>[] {
  const totalHours = heatmap.hours || 49;
  const collections: GeoJSON.FeatureCollection<GeoJSON.Point>[] = [];

  for (let h = 0; h < totalHours; h++) {
    const features: GeoJSON.Feature<GeoJSON.Point>[] = [];
    for (let p = 0; p < heatmap.points.length; p++) {
      const pt = heatmap.points[p];
      const level = pt.levels[h] ?? 0;
      // Only include points with weather risk or level > 0 for heatmap density, or include all with normalized weight
      features.push({
        type: 'Feature',
        properties: {
          level,
          weight: level / 4.0, // 0 to 1
        },
        geometry: {
          type: 'Point',
          coordinates: [pt.lng, pt.lat],
        },
      });
    }

    collections.push({
      type: 'FeatureCollection',
      features,
    });
  }

  return collections;
}
