import React from 'react';
import { useTripContext } from '../context/TripContext';
import { Truck, CloudLightning, RotateCcw } from 'lucide-react';

export const Header: React.FC = () => {
  const { tripData, resetTrip } = useTripContext();
  const isMock = import.meta.env.VITE_USE_MOCK === 'true';

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon-wrapper">
          <Truck className="brand-truck-icon" size={22} />
          <CloudLightning className="brand-weather-badge" size={14} />
        </div>
        <div className="brand-text">
          <h1 className="brand-title">StormHaul</h1>
          <span className="brand-subtitle">Weather-Aware Freight Routing</span>
        </div>
      </div>

      <div className="header-actions">
        <div className="status-indicator-pill">
          <span className={`status-dot ${isMock ? 'dot-mock' : 'dot-live'}`} />
          <span className="status-text">
            {isMock ? 'Mock / Fixture Mode' : 'Live Open-Meteo'}
          </span>
        </div>

        {tripData && (
          <button
            type="button"
            className="header-reset-btn"
            onClick={resetTrip}
            title="Start New Trip Analysis"
          >
            <RotateCcw size={14} />
            <span>New Trip</span>
          </button>
        )}
      </div>
    </header>
  );
};
