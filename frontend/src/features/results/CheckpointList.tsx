import React, { useRef, useEffect } from 'react';
import { useTripContext } from '../../context/TripContext';
import { formatLocalTime } from '../../lib/format';
import { getRiskColor, getRiskBgColor, formatRiskLabel } from '../../lib/risk';
import { Wind, CloudRain, Snowflake, AlertCircle, Compass } from 'lucide-react';

export const CheckpointList: React.FC = () => {
  const {
    selectedRoute,
    hoveredCheckpointIndex,
    setHoveredCheckpointIndex,
    setPopupCheckpoint,
  } = useTripContext();

  const itemRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Auto-scroll hovered checkpoint into view if hovered from map marker
  useEffect(() => {
    if (hoveredCheckpointIndex !== null && itemRefs.current[hoveredCheckpointIndex]) {
      itemRefs.current[hoveredCheckpointIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [hoveredCheckpointIndex]);

  if (!selectedRoute || !selectedRoute.checkpoints) {
    return null;
  }

  const checkpoints = selectedRoute.checkpoints;

  return (
    <div className="checkpoints-section">
      <div className="section-header">
        <div>
          <h3 className="section-title">Route Checkpoints ({checkpoints.length})</h3>
          <span className="section-hint">Hover to highlight waypoint on map</span>
        </div>
      </div>

      <div className="checkpoints-scroll-list">
        {checkpoints.map((chk) => {
          const isHovered = hoveredCheckpointIndex === chk.index;
          const riskColor = getRiskColor(chk.risk.level);
          const riskBg = getRiskBgColor(chk.risk.level);

          return (
            <div
              key={chk.index}
              ref={(el) => (itemRefs.current[chk.index] = el)}
              className={`checkpoint-item ${isHovered ? 'checkpoint-item-hovered' : ''}`}
              style={{
                borderLeftColor: riskColor,
                backgroundColor: isHovered ? riskBg : undefined,
              }}
              onMouseEnter={() => setHoveredCheckpointIndex(chk.index)}
              onMouseLeave={() => setHoveredCheckpointIndex(null)}
              onClick={() => setPopupCheckpoint(chk)}
            >
              <div className="chk-header">
                <div className="chk-mile-group">
                  <span className="chk-index">#{chk.index}</span>
                  <span className="chk-mile">Mile {chk.mile.toFixed(1)}</span>
                </div>
                <span
                  className="chk-risk-badge"
                  style={{
                    color: riskColor,
                    borderColor: riskColor,
                  }}
                >
                  {formatRiskLabel(chk.risk.level)}
                </span>
              </div>

              <div className="chk-eta-row">
                <span className="chk-eta-label">ETA:</span>
                <span className="chk-eta-value">{formatLocalTime(chk.eta)}</span>
              </div>

              <div className="chk-weather-row">
                <div className="chk-weather-chip" title="Sustained Wind & Gusts">
                  <Wind size={13} />
                  <span>
                    {chk.weather.wind_mph.toFixed(0)} mph
                    {chk.weather.gust_mph ? ` (g ${chk.weather.gust_mph.toFixed(0)})` : ''}
                  </span>
                </div>

                {chk.weather.rain_in_hr > 0 && (
                  <div className="chk-weather-chip" title="Precipitation / Rain">
                    <CloudRain size={13} />
                    <span>{chk.weather.rain_in_hr.toFixed(2)} in/h</span>
                  </div>
                )}

                {chk.weather.snow_in_hr > 0 && (
                  <div className="chk-weather-chip chk-weather-snow" title="Snowfall rate">
                    <Snowflake size={13} />
                    <span>{chk.weather.snow_in_hr.toFixed(1)} in/h</span>
                  </div>
                )}

                {chk.weather.rain_in_hr === 0 && chk.weather.snow_in_hr === 0 && (
                  <div className="chk-weather-chip chk-weather-dry" title="Dry">
                    <Compass size={13} />
                    <span>Dry</span>
                  </div>
                )}
              </div>

              {chk.risk.drivers && chk.risk.drivers.length > 0 && (
                <div className="chk-drivers">
                  <AlertCircle size={12} className="chk-driver-icon" />
                  <span>{chk.risk.drivers.join(' • ')}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
