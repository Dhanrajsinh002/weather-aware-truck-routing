import React from 'react';
import { useTripContext } from '../../context/TripContext';
import { RouteOption } from '../../types/api';
import { formatDistance, formatDuration, formatLocalTime } from '../../lib/format';
import { getRiskColor, formatRiskLabel } from '../../lib/risk';
import { ShieldCheck, Clock, Navigation, AlertTriangle, ShieldAlert } from 'lucide-react';

export const RouteCards: React.FC = () => {
  const { tripData, selectedRouteId, setSelectedRouteId } = useTripContext();

  if (!tripData || !tripData.routes || tripData.routes.length === 0) {
    return null;
  }

  return (
    <div className="route-cards-container">
      <div className="section-header">
        <h3 className="section-title">Available Routes ({tripData.routes.length})</h3>
        <span className="section-hint">Select a route to inspect segment risks</span>
      </div>

      <div className="route-cards-list">
        {tripData.routes.map((route: RouteOption) => {
          const isSelected = route.id === selectedRouteId;
          const lastCheckpoint = route.checkpoints[route.checkpoints.length - 1];
          const hasNoTravel = route.metrics.no_travel_miles > 0;

          return (
            <div
              key={route.id}
              className={`route-card ${isSelected ? 'route-card-selected' : ''} ${
                route.recommended ? 'route-card-recommended' : ''
              }`}
              onClick={() => setSelectedRouteId(route.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setSelectedRouteId(route.id);
                }
              }}
              aria-pressed={isSelected}
            >
              <div className="route-card-header">
                <div className="route-label-group">
                  <span className="route-rank-tag">Option {route.rank}</span>
                  <h4 className="route-name">{route.label}</h4>
                </div>

                {route.recommended && (
                  <span className="badge-recommended">
                    <ShieldCheck size={14} /> Recommended
                  </span>
                )}
              </div>

              <div className="route-stats-grid">
                <div className="stat-item">
                  <Navigation size={14} className="stat-icon" />
                  <span className="stat-value">{formatDistance(route.distance_miles)}</span>
                </div>
                <div className="stat-item">
                  <Clock size={14} className="stat-icon" />
                  <span className="stat-value">{formatDuration(route.duration_seconds)}</span>
                </div>
                {lastCheckpoint && (
                  <div className="stat-item stat-item-eta">
                    <span className="stat-label">ETA:</span>
                    <span className="stat-value-sm">{formatLocalTime(lastCheckpoint.eta)}</span>
                  </div>
                )}
              </div>

              {/* Weather Risk Miles Breakdown */}
              <div className="risk-metrics-strip">
                <div className="metric-chip" style={{ borderLeftColor: getRiskColor('LOW') }}>
                  <span className="metric-title">Avg Risk</span>
                  <span className="metric-value font-mono">{route.metrics.avg_risk.toFixed(2)}</span>
                </div>

                <div
                  className={`metric-chip ${route.metrics.severe_miles > 0 ? 'metric-chip-severe' : ''}`}
                  style={{ borderLeftColor: getRiskColor('SEVERE') }}
                >
                  <span className="metric-title">Severe</span>
                  <span className="metric-value font-mono">{route.metrics.severe_miles.toFixed(1)} mi</span>
                </div>

                <div
                  className={`metric-chip ${route.metrics.high_miles > 0 ? 'metric-chip-high' : ''}`}
                  style={{ borderLeftColor: getRiskColor('HIGH') }}
                >
                  <span className="metric-title">High</span>
                  <span className="metric-value font-mono">{route.metrics.high_miles.toFixed(1)} mi</span>
                </div>

                {hasNoTravel && (
                  <div
                    className="metric-chip metric-chip-notravel"
                    style={{ borderLeftColor: getRiskColor('NO_TRAVEL') }}
                  >
                    <span className="metric-title">No Travel</span>
                    <span className="metric-value font-mono">{route.metrics.no_travel_miles.toFixed(1)} mi</span>
                  </div>
                )}
              </div>

              {/* Risk Alert Tag if severe or no travel */}
              {hasNoTravel ? (
                <div className="hazard-warning-tag hazard-no-travel">
                  <ShieldAlert size={14} />
                  <span>Unsafe: Contains {route.metrics.no_travel_miles.toFixed(1)} mi No-Travel weather</span>
                </div>
              ) : route.metrics.severe_miles > 0 ? (
                <div className="hazard-warning-tag hazard-severe">
                  <AlertTriangle size={14} />
                  <span>Caution: Max risk level {formatRiskLabel(route.metrics.max_level)}</span>
                </div>
              ) : (
                <div className="hazard-warning-tag hazard-safe">
                  <ShieldCheck size={14} />
                  <span>Favorable weather profile ({formatRiskLabel(route.metrics.max_level)})</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
