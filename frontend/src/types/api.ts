export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE' | 'NO_TRAVEL';

export const RISK_NUMERIC_MAP: Record<RiskLevel, number> = {
  LOW: 0,
  MODERATE: 1,
  HIGH: 2,
  SEVERE: 3,
  NO_TRAVEL: 4,
};

export const NUMERIC_TO_RISK_MAP: Record<number, RiskLevel> = {
  0: 'LOW',
  1: 'MODERATE',
  2: 'HIGH',
  3: 'SEVERE',
  4: 'NO_TRAVEL',
};

export interface GeocodeLocation {
  label: string;
  lat: number;
  lng: number;
}

export interface GeocodeResponse {
  results: GeocodeLocation[];
}

export type IntervalSelection = 'auto' | 10 | 25 | 50;

export interface AnalyzeRequest {
  origin: {
    lat: number;
    lng: number;
    label: string;
  };
  destination: {
    lat: number;
    lng: number;
    label: string;
  };
  departure_time: string; // ISO 8601 UTC
  load_weight_lb: number;
  checkpoint_interval_miles: IntervalSelection;
}

export interface WeatherData {
  wind_mph: number;
  gust_mph?: number;
  rain_in_hr: number;
  snow_in_hr: number;
}

export interface RiskData {
  level: RiskLevel;
  score: number;
  drivers: string[];
}

export interface Checkpoint {
  index: number;
  mile: number;
  lat: number;
  lng: number;
  eta: string;
  weather: WeatherData;
  risk: RiskData;
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: [number, number][]; // [lng, lat]
}

export interface RouteMetrics {
  no_travel_miles: number;
  severe_miles: number;
  high_miles: number;
  avg_risk: number;
  max_level: RiskLevel;
}

export interface RouteOption {
  id: string;
  label: string;
  distance_miles: number;
  duration_seconds: number;
  geometry: GeoJSONLineString;
  metrics: RouteMetrics;
  checkpoints: Checkpoint[];
  rank: number;
  recommended: boolean;
}

export interface Recommendation {
  route_id: string;
  reasons: string[];
  warnings: string[];
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  levels: number[]; // 49 integer levels (0 to 4)
}

export interface HeatmapData {
  start_time: string;
  hours: number;
  points: HeatmapPoint[];
}

export interface AnalyzeResponse {
  request_id: string;
  weather_mode: string;
  interval_miles: number;
  routes: RouteOption[];
  recommendation: Recommendation;
  heatmap: HeatmapData;
}

export interface ApiError {
  error: {
    code: string;
    message?: string;
    fields?: Record<string, string[] | string>;
    provider?: string;
  };
}
