import { AnalyzeRequest, AnalyzeResponse, GeocodeResponse } from '../types/api';
import sampleAnalyzeData from '../mocks/analyze.sample.json';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const MOCK_GEOCODE_DB = [
  { label: 'Chicago, Illinois, USA', lat: 41.8781, lng: -87.6298 },
  { label: 'Denver, Colorado, USA', lat: 39.7392, lng: -104.9903 },
  { label: 'Omaha, Nebraska, USA', lat: 41.2565, lng: -95.9345 },
  { label: 'Des Moines, Iowa, USA', lat: 41.6005, lng: -93.6091 },
  { label: 'Lincoln, Nebraska, USA', lat: 40.8136, lng: -96.7026 },
  { label: 'Kansas City, Missouri, USA', lat: 39.0997, lng: -94.5786 },
  { label: 'Cheyenne, Wyoming, USA', lat: 41.1399, lng: -104.8202 },
  { label: 'Dallas, Texas, USA', lat: 32.7767, lng: -96.7970 },
  { label: 'Minneapolis, Minnesota, USA', lat: 44.9778, lng: -93.2650 },
  { label: 'Salt Lake City, Utah, USA', lat: 40.7608, lng: -111.8910 },
];

export async function searchGeocode(query: string, signal?: AbortSignal): Promise<GeocodeResponse> {
  const trimmed = query.trim();
  if (!trimmed || trimmed.length < 2) {
    return { results: [] };
  }

  if (USE_MOCK) {
    // Simulate short network latency
    await new Promise((resolve) => setTimeout(resolve, 150));
    const lower = trimmed.toLowerCase();
    const filtered = MOCK_GEOCODE_DB.filter((item) =>
      item.label.toLowerCase().includes(lower)
    );
    if (filtered.length > 0) {
      return { results: filtered };
    }
    // If not found in simple mock DB, provide query as custom location or call backend
    return {
      results: [
        { label: `${trimmed} (Mock Location)`, lat: 40.0, lng: -95.0 },
      ],
    };
  }

  const response = await fetch(`/api/geocode/?q=${encodeURIComponent(trimmed)}`, {
    signal,
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Geocoding failed with status ${response.status}`);
  }

  return response.json();
}

export async function analyzeTrip(
  request: AnalyzeRequest,
  signal?: AbortSignal
): Promise<AnalyzeResponse> {
  if (USE_MOCK) {
    // Simulate brief network calculation delay
    await new Promise((resolve, reject) => {
      const timer = setTimeout(resolve, 400);
      if (signal) {
        signal.addEventListener('abort', () => {
          clearTimeout(timer);
          reject(new DOMException('Aborted', 'AbortError'));
        });
      }
    });

    // Deep clone sample data so client modifications don't mutate mock
    const cloned = JSON.parse(JSON.stringify(sampleAnalyzeData)) as AnalyzeResponse;
    // Align start time with the user's departure time
    cloned.heatmap.start_time = request.departure_time;
    return cloned;
  }

  const response = await fetch('/api/analyze/', {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorData: { error?: { message?: string; code?: string } } | null = null;
    try {
      errorData = (await response.json()) as { error?: { message?: string; code?: string } };
    } catch {
      // ignore json parse error
    }

    if (errorData?.error?.message) {
      throw new Error(errorData.error.message);
    }
    if (errorData?.error?.code) {
      throw new Error(`Error: ${errorData.error.code}`);
    }
    throw new Error(`Analyze request failed with status ${response.status}`);
  }

  return response.json();
}
