import React, { useEffect, useRef } from 'react';
import { useTripContext } from '../../context/TripContext';
import {
  clampSliderHour,
  nextSliderHour,
  prevSliderHour,
  formatSliderTimeLabel,
  MAX_SLIDER_HOUR,
} from './sliderLogic';
import { Play, Pause, ChevronLeft, ChevronRight, Clock, Flame } from 'lucide-react';

export const HeatmapSlider: React.FC = () => {
  const {
    tripData,
    sliderHour,
    setSliderHour,
    isPlaying,
    setIsPlaying,
    showHeatmap,
    setShowHeatmap,
  } = useTripContext();

  const playTimerRef = useRef<NodeJS.Timeout | null>(null);

  const startTimeIso = tripData?.heatmap?.start_time || new Date().toISOString();
  const maxHours = tripData?.heatmap?.hours ? tripData.heatmap.hours - 1 : MAX_SLIDER_HOUR;

  // Animation playback (4 steps / sec = 250ms per step)
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setSliderHour((curr) => nextSliderHour(curr, maxHours, true));
      }, 250);
    } else {
      if (playTimerRef.current) {
        clearInterval(playTimerRef.current);
        playTimerRef.current = null;
      }
    }

    return () => {
      if (playTimerRef.current) {
        clearInterval(playTimerRef.current);
      }
    };
  }, [isPlaying, maxHours, setSliderHour]);

  // Keyboard navigation for arrow keys and spacebar
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault();
      setIsPlaying(false);
      setSliderHour((curr) => prevSliderHour(curr));
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault();
      setIsPlaying(false);
      setSliderHour((curr) => nextSliderHour(curr, maxHours, false));
    } else if (e.key === ' ') {
      e.preventDefault();
      setIsPlaying((p) => !p);
    }
  };

  const { offsetLabel, localTimeLabel } = formatSliderTimeLabel(startTimeIso, sliderHour);

  if (!tripData || !tripData.heatmap) {
    return null;
  }

  const progressPercent = (sliderHour / maxHours) * 100;

  return (
    <div className="bottom-heatmap-bar">
      <div className="heatmap-bar-inner">
        {/* Playback Controls & Info */}
        <div className="heatmap-control-strip">
          <div className="playback-buttons">
            <button
              type="button"
              className="ctrl-btn"
              onClick={() => {
                setIsPlaying(false);
                setSliderHour((curr) => prevSliderHour(curr));
              }}
              title="Step backward 1 hour (Arrow Left)"
              aria-label="Step backward 1 hour"
            >
              <ChevronLeft size={16} />
            </button>

            <button
              type="button"
              className={`ctrl-btn ctrl-btn-play ${isPlaying ? 'ctrl-btn-playing' : ''}`}
              onClick={() => setIsPlaying((p) => !p)}
              title={isPlaying ? 'Pause (Space)' : 'Play 48h forecast timeline (Space)'}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} className="play-icon-offset" />}
            </button>

            <button
              type="button"
              className="ctrl-btn"
              onClick={() => {
                setIsPlaying(false);
                setSliderHour((curr) => nextSliderHour(curr, maxHours, false));
              }}
              title="Step forward 1 hour (Arrow Right)"
              aria-label="Step forward 1 hour"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="time-display-badge">
            <Clock size={15} className="clock-icon" />
            <span className="time-offset-tag">{offsetLabel}</span>
            <span className="time-divider">•</span>
            <span className="time-local-tag">{localTimeLabel}</span>
          </div>

          <div className="heatmap-mode-indicator">
            <button
              type="button"
              className={`heatmap-status-chip ${showHeatmap ? 'chip-active' : ''}`}
              onClick={() => setShowHeatmap((prev) => !prev)}
              title="Toggle Heatmap Layer"
            >
              <Flame size={13} />
              <span>{showHeatmap ? 'Corridor Heatmap Active' : 'Heatmap Hidden'}</span>
            </button>
          </div>
        </div>

        {/* Slider Track */}
        <div className="slider-track-container">
          <span className="slider-edge-label">0h</span>
          <div className="slider-input-wrapper">
            <input
              type="range"
              min={0}
              max={maxHours}
              step={1}
              value={sliderHour}
              onChange={(e) => {
                setIsPlaying(false);
                setSliderHour(clampSliderHour(parseInt(e.target.value, 10), 0, maxHours));
              }}
              onKeyDown={handleKeyDown}
              className="time-range-slider"
              aria-label="Weather forecast time slider"
              style={{
                background: `linear-gradient(to right, #3b82f6 ${progressPercent}%, rgba(255, 255, 255, 0.12) ${progressPercent}%)`,
              }}
            />
            {/* Hour tick marks */}
            <div className="slider-ticks">
              {[0, 6, 12, 18, 24, 30, 36, 42, 48].map((tick) => (
                <div
                  key={tick}
                  className="slider-tick"
                  style={{ left: `${(tick / maxHours) * 100}%` }}
                >
                  <span className="tick-label">{tick}h</span>
                </div>
              ))}
            </div>
          </div>
          <span className="slider-edge-label">+{maxHours}h</span>
        </div>
      </div>
    </div>
  );
};
