import React, { useState } from 'react';
import { Header } from './components/Header';
import { TripForm } from './features/planner/TripForm';
import { RouteCards } from './features/results/RouteCards';
import { RecommendationBanner } from './features/results/RecommendationBanner';
import { CheckpointList } from './features/results/CheckpointList';
import { MapContainer } from './features/map/MapContainer';
import { HeatmapSlider } from './features/heatmap/HeatmapSlider';
import { useTripContext } from './context/TripContext';
import { SlidersHorizontal, Map, ListCollapse } from 'lucide-react';

export const AppContent: React.FC = () => {
  const { tripData } = useTripContext();
  const [activeTabMobile, setActiveTabMobile] = useState<'panel' | 'map'>('panel');
  const [showEditForm, setShowEditForm] = useState(false);

  return (
    <div className="app-container">
      <Header />

      {/* Mobile Tab Switcher */}
      <div className="mobile-tab-bar">
        <button
          type="button"
          className={`mobile-tab-btn ${activeTabMobile === 'panel' ? 'tab-active' : ''}`}
          onClick={() => setActiveTabMobile('panel')}
        >
          <SlidersHorizontal size={16} />
          <span>{tripData ? 'Results & Form' : 'Trip Planner'}</span>
        </button>
        <button
          type="button"
          className={`mobile-tab-btn ${activeTabMobile === 'map' ? 'tab-active' : ''}`}
          onClick={() => setActiveTabMobile('map')}
        >
          <Map size={16} />
          <span>Map & Corridor</span>
        </button>
      </div>

      <div className="app-main">
        {/* Left Panel: Form + Results */}
        <aside className={`sidebar-panel ${activeTabMobile === 'panel' ? 'panel-visible-mobile' : ''}`}>
          {!tripData ? (
            <div className="planner-scroll-view">
              <TripForm />
            </div>
          ) : (
            <div className="results-scroll-view">
              <div className="edit-form-toggle-wrapper">
                <button
                  type="button"
                  className="edit-trip-toggle-btn"
                  onClick={() => setShowEditForm((prev) => !prev)}
                >
                  <ListCollapse size={16} />
                  <span>{showEditForm ? 'Hide Trip Parameters' : 'Edit Trip & Recalculate'}</span>
                </button>
              </div>

              {showEditForm && (
                <div className="embedded-form-box">
                  <TripForm />
                </div>
              )}

              <RecommendationBanner />
              <RouteCards />
              <CheckpointList />
            </div>
          )}
        </aside>

        {/* Map Center Area */}
        <main className={`map-area ${activeTabMobile === 'map' ? 'map-visible-mobile' : ''}`}>
          <MapContainer />
          {tripData && <HeatmapSlider />}
        </main>
      </div>
    </div>
  );
};

export default AppContent;
