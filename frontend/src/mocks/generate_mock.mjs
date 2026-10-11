import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const depTime = new Date('2026-10-12T14:00:00Z');

function interpolateLine(pts, count) {
  const coords = [];
  const segments = pts.length - 1;
  const segCount = Math.max(2, Math.floor(count / segments));

  for (let i = 0; i < segments; i++) {
    const p1 = pts[i];
    const p2 = pts[i + 1];
    for (let s = 0; s < segCount; s++) {
      const t = s / segCount;
      const lng = Number((p1[0] + (p2[0] - p1[0]) * t).toFixed(5));
      const lat = Number((p1[1] + (p2[1] - p1[1]) * t).toFixed(5));
      coords.push([lng, lat]);
    }
  }
  coords.push(pts[pts.length - 1]);
  return coords;
}

// Route 1: I-80 / I-76 via Des Moines, Omaha, Lincoln, Sterling
const r1Pts = [
  [-87.6298, 41.8781], [-88.08, 41.52], [-90.57, 41.52], [-91.53, 41.66],
  [-93.60, 41.60], [-95.93, 41.25], [-96.70, 40.81], [-98.34, 40.92],
  [-100.76, 41.12], [-101.71, 41.12], [-102.26, 40.98], [-103.20, 40.62],
  [-103.79, 40.25], [-104.9903, 39.7392]
];
const r1Coords = interpolateLine(r1Pts, 130);

// Route 2: I-80 via North Platte & Cheyenne
const r2Pts = [
  [-87.6298, 41.8781], [-88.08, 41.52], [-90.57, 41.52], [-91.53, 41.66],
  [-93.60, 41.60], [-95.93, 41.25], [-96.70, 40.81], [-98.34, 40.92],
  [-100.76, 41.12], [-102.00, 41.20], [-103.50, 41.15], [-104.82, 41.13],
  [-104.90, 40.50], [-104.9903, 39.7392]
];
const r2Coords = interpolateLine(r2Pts, 130);

// Route 3: Southern route via I-72 / I-70 (Springfield, Kansas City, Topeka, Salina, Limon, Denver)
const r3Pts = [
  [-87.6298, 41.8781], [-88.50, 41.20], [-89.65, 39.80], [-91.35, 39.70],
  [-93.00, 39.30], [-94.57, 39.09], [-95.68, 39.05], [-97.61, 38.84],
  [-100.80, 39.35], [-103.69, 39.26], [-104.9903, 39.7392]
];
const r3Coords = interpolateLine(r3Pts, 130);

function makeCheckpoints(coords, totalMiles, profile, durationSeconds) {
  const chkpts = [];
  const n = 41; // ~40 checkpoints
  const mileStep = totalMiles / (n - 1);
  const timeStep = durationSeconds / (n - 1);

  for (let i = 0; i < n; i++) {
    const frac = i / (n - 1);
    const coordIdx = Math.min(coords.length - 1, Math.floor(frac * (coords.length - 1)));
    const [lng, lat] = coords[coordIdx];
    const mile = Number((i * mileStep).toFixed(1));
    const etaDate = new Date(depTime.getTime() + i * timeStep * 1000);
    const eta = etaDate.toISOString();

    let prof = profile[0];
    for (const p of profile) {
      if (frac <= p.frac) {
        prof = p;
        break;
      }
    }

    chkpts.push({
      index: i,
      mile,
      lat: Number(lat.toFixed(4)),
      lng: Number(lng.toFixed(4)),
      eta,
      weather: {
        wind_mph: prof.wind,
        gust_mph: prof.gust,
        rain_in_hr: prof.rain,
        snow_in_hr: prof.snow,
      },
      risk: {
        level: prof.level,
        score: prof.score,
        drivers: prof.driver ? [prof.driver] : [],
      },
    });
  }
  return chkpts;
}

// Profiles: fraction, level, score, wind, gust, rain, snow, driver
const r1Profile = [
  { frac: 0.22, level: 'LOW', score: 0, wind: 14.2, gust: 19.5, rain: 0.0, snow: 0.0, driver: '' },
  { frac: 0.42, level: 'MODERATE', score: 1, wind: 28.5, gust: 34.0, rain: 0.16, snow: 0.0, driver: 'Moderate rain 0.16 in/hr & wind 28.5 mph' },
  { frac: 0.68, level: 'LOW', score: 0, wind: 18.0, gust: 24.0, rain: 0.0, snow: 0.0, driver: '' },
  { frac: 0.86, level: 'HIGH', score: 2, wind: 38.0, gust: 48.0, rain: 0.0, snow: 0.0, driver: 'Sustained wind 38.0 mph, gusts up to 48 mph' },
  { frac: 0.93, level: 'SEVERE', score: 3, wind: 46.5, gust: 54.0, rain: 0.0, snow: 0.8, driver: 'Wind 46.5 mph + load 42,000 lb → Severe' },
  { frac: 1.00, level: 'MODERATE', score: 1, wind: 26.0, gust: 32.0, rain: 0.0, snow: 0.3, driver: 'Light snow 0.3 in/hr' },
];

const r2Profile = [
  { frac: 0.20, level: 'LOW', score: 0, wind: 15.0, gust: 20.0, rain: 0.0, snow: 0.0, driver: '' },
  { frac: 0.44, level: 'MODERATE', score: 1, wind: 29.0, gust: 36.0, rain: 0.12, snow: 0.0, driver: 'Moderate rain 0.12 in/hr' },
  { frac: 0.65, level: 'HIGH', score: 2, wind: 39.5, gust: 49.0, rain: 0.0, snow: 0.0, driver: 'High crosswind 39.5 mph across open plains' },
  { frac: 0.88, level: 'SEVERE', score: 3, wind: 48.0, gust: 56.0, rain: 0.0, snow: 1.4, driver: 'Wind 48.0 mph + load 42,000 lb → Severe' },
  { frac: 1.00, level: 'HIGH', score: 2, wind: 36.0, gust: 44.0, rain: 0.0, snow: 0.7, driver: 'Wind 36.0 mph with snow 0.7 in/hr' },
];

const r3Profile = [
  { frac: 0.25, level: 'LOW', score: 0, wind: 12.0, gust: 18.0, rain: 0.0, snow: 0.0, driver: '' },
  { frac: 0.48, level: 'MODERATE', score: 1, wind: 27.0, gust: 34.0, rain: 0.22, snow: 0.0, driver: 'Rain 0.22 in/hr' },
  { frac: 0.68, level: 'HIGH', score: 2, wind: 37.0, gust: 46.0, rain: 0.0, snow: 0.6, driver: 'High wind 37.0 mph & snow' },
  { frac: 0.82, level: 'SEVERE', score: 3, wind: 47.0, gust: 53.0, rain: 0.0, snow: 2.4, driver: 'Heavy snow 2.4 in/hr + wind 47.0 mph → Severe' },
  { frac: 0.94, level: 'NO_TRAVEL', score: 4, wind: 56.5, gust: 68.0, rain: 0.0, snow: 3.5, driver: 'Wind 56.5 mph ≥ 55 mph & heavy snow 3.5 in/hr → No Travel' },
  { frac: 1.00, level: 'HIGH', score: 2, wind: 38.0, gust: 45.0, rain: 0.0, snow: 0.8, driver: 'Blowing snow and wind 38.0 mph' },
];

const r1Checkpoints = makeCheckpoints(r1Coords, 1003.2, r1Profile, 54000);
const r2Checkpoints = makeCheckpoints(r2Coords, 1025.5, r2Profile, 55800);
const r3Checkpoints = makeCheckpoints(r3Coords, 1054.0, r3Profile, 58320);

// Generate corridor heatmap points
const heatmapPoints = [];
const lats = [39.2, 39.8, 40.4, 41.0, 41.6, 42.2];
const lngs = [-87.6, -89.0, -90.5, -92.0, -93.5, -95.0, -96.5, -98.0, -99.5, -101.0, -102.5, -103.8, -105.0];

for (const lat of lats) {
  for (const lng of lngs) {
    const levels = [];
    for (let h = 0; h < 49; h++) {
      // Storm system progression west to east
      const stormCenterLng = -104.5 + (h / 48) * 15.0;
      const stormCenterLat = 40.3 + Math.sin(h / 8) * 0.7;
      const dist = Math.hypot((lng - stormCenterLng) * 1.25, (lat - stormCenterLat) * 2.0);

      let lvl = 0;
      if (dist < 1.1) {
        lvl = (h >= 8 && h <= 26 && lat < 40.6) ? 4 : 3;
      } else if (dist < 2.1) {
        lvl = h % 2 === 0 ? 3 : 2;
      } else if (dist < 3.4) {
        lvl = dist < 2.8 ? 2 : 1;
      } else if (dist < 5.0) {
        lvl = lat > 40.2 ? 1 : 0;
      } else {
        lvl = 0;
      }
      levels.push(lvl);
    }

    heatmapPoints.push({
      lat: Number(lat.toFixed(2)),
      lng: Number(lng.toFixed(2)),
      levels,
    });
  }
}

const mockResponse = {
  request_id: 'sample-req-chicago-denver',
  weather_mode: 'fixture',
  interval_miles: 25,
  routes: [
    {
      id: 'r1',
      label: 'I-80 / I-76 (Fastest)',
      distance_miles: 1003.2,
      duration_seconds: 54000,
      geometry: {
        type: 'LineString',
        coordinates: r1Coords,
      },
      metrics: {
        no_travel_miles: 0.0,
        severe_miles: 12.5,
        high_miles: 40.0,
        avg_risk: 0.84,
        max_level: 'SEVERE',
      },
      checkpoints: r1Checkpoints,
      rank: 1,
      recommended: true,
    },
    {
      id: 'r2',
      label: 'I-80 via North Platte & Cheyenne',
      distance_miles: 1025.5,
      duration_seconds: 55800,
      geometry: {
        type: 'LineString',
        coordinates: r2Coords,
      },
      metrics: {
        no_travel_miles: 0.0,
        severe_miles: 31.0,
        high_miles: 65.0,
        avg_risk: 1.45,
        max_level: 'SEVERE',
      },
      checkpoints: r2Checkpoints,
      rank: 2,
      recommended: false,
    },
    {
      id: 'r3',
      label: 'Southern Route via I-72 / I-70',
      distance_miles: 1054.0,
      duration_seconds: 58320,
      geometry: {
        type: 'LineString',
        coordinates: r3Coords,
      },
      metrics: {
        no_travel_miles: 15.0,
        severe_miles: 44.2,
        high_miles: 50.0,
        avg_risk: 2.12,
        max_level: 'NO_TRAVEL',
      },
      checkpoints: r3Checkpoints,
      rank: 3,
      recommended: false,
    },
  ],
  recommendation: {
    route_id: 'r1',
    reasons: [
      'Fewest Severe miles (12.5 mi vs 31.0 mi on Route 2, 44.2 mi on Route 3)',
      'Zero No-Travel miles (Route 3 has 15.0 mi of No-Travel conditions)',
      'Lowest corridor average risk score (0.84 vs 1.45, 2.12)',
      'Fastest transit duration (15h 00m vs 15h 30m, 16h 12m)',
    ],
    warnings: [
      'Route 3 encounters severe winter blizzard with No Travel restrictions near Limon, CO.',
    ],
  },
  heatmap: {
    start_time: '2026-10-12T14:00:00Z',
    hours: 49,
    points: heatmapPoints,
  },
};

const outPath = path.join(__dirname, 'analyze.sample.json');
fs.writeFileSync(outPath, JSON.stringify(mockResponse, null, 2), 'utf-8');
console.log('Successfully wrote analyze.sample.json to', outPath);
