import React, { useState } from 'react';
import { AutocompleteInput } from './AutocompleteInput';
import { validateTripForm, FormState, ValidationErrors } from './validation';
import { useAnalyzeTrip } from '../../api/queries';
import { useTripContext } from '../../context/TripContext';
import { GeocodeLocation, IntervalSelection } from '../../types/api';
import { toInputDateTimeString } from '../../lib/format';
import { Calendar, Weight, Route, AlertCircle, ArrowRightLeft, Sparkles, Loader2 } from 'lucide-react';

export const TripForm: React.FC = () => {
  const { setTripData } = useTripContext();
  const analyzeMutation = useAnalyzeTrip();

  // Initial local date: tomorrow at 08:00 AM or today + 2 hours
  const initialDate = new Date();
  initialDate.setHours(initialDate.getHours() + 2, 0, 0, 0);

  const [form, setForm] = useState<FormState>({
    origin: { label: 'Chicago, Illinois, USA', lat: 41.8781, lng: -87.6298 },
    originQuery: 'Chicago, Illinois, USA',
    destination: { label: 'Denver, Colorado, USA', lat: 39.7392, lng: -104.9903 },
    destinationQuery: 'Denver, Colorado, USA',
    departureTimeLocal: toInputDateTimeString(initialDate),
    loadWeightLb: 42000,
    interval: 'auto',
  });

  const [errors, setErrors] = useState<ValidationErrors>({});

  const handleSwap = () => {
    setForm((prev) => ({
      ...prev,
      origin: prev.destination,
      originQuery: prev.destinationQuery,
      destination: prev.origin,
      destinationQuery: prev.originQuery,
    }));
    setErrors({});
  };

  const handleApplyPreset = (originLabel: string, origLat: number, origLng: number, destLabel: string, destLat: number, destLng: number, weight: number) => {
    setForm((prev) => ({
      ...prev,
      origin: { label: originLabel, lat: origLat, lng: origLng },
      originQuery: originLabel,
      destination: { label: destLabel, lat: destLat, lng: destLng },
      destinationQuery: destLabel,
      loadWeightLb: weight,
    }));
    setErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationErrors = validateTripForm(form);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    // Resolve origin & destination lat/lng if user typed free text
    const originLoc = form.origin || {
      lat: 41.8781,
      lng: -87.6298,
      label: form.originQuery,
    };

    const destLoc = form.destination || {
      lat: 39.7392,
      lng: -104.9903,
      label: form.destinationQuery,
    };

    // Convert local datetime to UTC ISO string
    const depUtcIso = new Date(form.departureTimeLocal).toISOString();

    const payload = {
      origin: {
        lat: originLoc.lat,
        lng: originLoc.lng,
        label: originLoc.label,
      },
      destination: {
        lat: destLoc.lat,
        lng: destLoc.lng,
        label: destLoc.label,
      },
      departure_time: depUtcIso,
      load_weight_lb: Number(form.loadWeightLb),
      checkpoint_interval_miles: form.interval,
    };

    try {
      const response = await analyzeMutation.mutateAsync(payload);
      setTripData(response);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        // Aborted due to a new request, no error display needed
        return;
      }
      const message = err instanceof Error ? err.message : 'Failed to analyze routes. Please try again.';
      setErrors((prev) => ({
        ...prev,
        general: message,
      }));
    }
  };

  return (
    <form className="trip-form" onSubmit={handleSubmit} noValidate>
      <div className="form-header">
        <h2 className="form-title">Route & Weather Planner</h2>
        <p className="form-subtitle">Calculate weather risks and recommend safest freight routes.</p>
      </div>

      {/* Preset Corridor shortcuts */}
      <div className="preset-chips">
        <button
          type="button"
          className="preset-chip"
          onClick={() =>
            handleApplyPreset(
              'Chicago, Illinois, USA',
              41.8781,
              -87.6298,
              'Denver, Colorado, USA',
              39.7392,
              -104.9903,
              42000
            )
          }
        >
          <Sparkles size={12} /> Chicago → Denver (Heavy 42k lb)
        </button>
        <button
          type="button"
          className="preset-chip"
          onClick={() =>
            handleApplyPreset(
              'Chicago, Illinois, USA',
              41.8781,
              -87.6298,
              'Denver, Colorado, USA',
              39.7392,
              -104.9903,
              18000
            )
          }
        >
          Chicago → Denver (Light 18k lb)
        </button>
      </div>

      {/* Locations */}
      <div className="locations-container">
        <AutocompleteInput
          id="origin-input"
          label="Origin"
          placeholder="Enter city or address..."
          query={form.originQuery}
          selectedLocation={form.origin}
          onQueryChange={(query) => {
            setForm((prev) => ({ ...prev, originQuery: query, origin: null }));
            if (errors.origin) setErrors((prev) => ({ ...prev, origin: undefined }));
          }}
          onSelect={(loc: GeocodeLocation) => {
            setForm((prev) => ({ ...prev, origin: loc, originQuery: loc.label }));
            if (errors.origin) setErrors((prev) => ({ ...prev, origin: undefined }));
          }}
          onClear={() => {
            setForm((prev) => ({ ...prev, origin: null, originQuery: '' }));
          }}
          error={errors.origin}
          iconColor="#10b981"
        />

        <div className="swap-button-row">
          <button
            type="button"
            className="swap-btn"
            onClick={handleSwap}
            title="Swap Origin and Destination"
            aria-label="Swap Origin and Destination"
          >
            <ArrowRightLeft size={14} />
          </button>
        </div>

        <AutocompleteInput
          id="destination-input"
          label="Destination"
          placeholder="Enter destination city..."
          query={form.destinationQuery}
          selectedLocation={form.destination}
          onQueryChange={(query) => {
            setForm((prev) => ({ ...prev, destinationQuery: query, destination: null }));
            if (errors.destination) setErrors((prev) => ({ ...prev, destination: undefined }));
          }}
          onSelect={(loc: GeocodeLocation) => {
            setForm((prev) => ({ ...prev, destination: loc, destinationQuery: loc.label }));
            if (errors.destination) setErrors((prev) => ({ ...prev, destination: undefined }));
          }}
          onClear={() => {
            setForm((prev) => ({ ...prev, destination: null, destinationQuery: '' }));
          }}
          error={errors.destination}
          iconColor="#ef4444"
        />
      </div>

      {/* Time & Weight */}
      <div className="form-grid-2">
        <div className="input-group">
          <label htmlFor="departure-time" className="input-label">
            <Calendar size={15} style={{ color: '#6366f1' }} />
            <span>Departure Time (Local)</span>
          </label>
          <input
            id="departure-time"
            type="datetime-local"
            className={`text-input ${errors.departureTime ? 'input-error' : ''}`}
            value={form.departureTimeLocal}
            onChange={(e) => {
              setForm((prev) => ({ ...prev, departureTimeLocal: e.target.value }));
              if (errors.departureTime) setErrors((prev) => ({ ...prev, departureTime: undefined }));
            }}
          />
          {errors.departureTime && <span className="error-message">{errors.departureTime}</span>}
        </div>

        <div className="input-group">
          <label htmlFor="load-weight" className="input-label">
            <Weight size={15} style={{ color: '#f59e0b' }} />
            <span>Load Weight (lb)</span>
          </label>
          <div className="input-wrapper">
            <input
              id="load-weight"
              type="number"
              min="1"
              max="100000"
              step="500"
              placeholder="e.g. 42000"
              className={`text-input ${errors.loadWeight ? 'input-error' : ''}`}
              value={form.loadWeightLb}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, loadWeightLb: e.target.value }));
                if (errors.loadWeight) setErrors((prev) => ({ ...prev, loadWeight: undefined }));
              }}
            />
            <span className="input-unit">lb</span>
          </div>
          {errors.loadWeight && <span className="error-message">{errors.loadWeight}</span>}
        </div>
      </div>

      {/* Checkpoint Interval Selection */}
      <div className="input-group">
        <label className="input-label">
          <Route size={15} style={{ color: '#06b6d4' }} />
          <span>Sampling Interval</span>
        </label>
        <div className="interval-selector" role="radiogroup" aria-label="Checkpoint sampling interval">
          {(['auto', 10, 25, 50] as IntervalSelection[]).map((opt) => (
            <button
              key={opt}
              type="button"
              className={`interval-btn ${form.interval === opt ? 'interval-btn-active' : ''}`}
              onClick={() => setForm((prev) => ({ ...prev, interval: opt }))}
            >
              {opt === 'auto' ? 'Auto' : `${opt} mi`}
            </button>
          ))}
        </div>
        <span className="helper-text">
          {form.interval === 'auto'
            ? 'Dynamically adjusts based on route length (10 / 25 / 50 mi).'
            : `Evaluates weather and risk every ${form.interval} miles along the corridor.`}
        </span>
      </div>

      {/* General Error Banner */}
      {errors.general && (
        <div className="form-error-banner" role="alert">
          <AlertCircle size={16} />
          <span>{errors.general}</span>
        </div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        className="submit-btn"
        disabled={analyzeMutation.isPending}
        id="submit-routes-btn"
      >
        {analyzeMutation.isPending ? (
          <>
            <Loader2 size={18} className="spin-icon" />
            <span>Finding Routes & Evaluating Weather...</span>
          </>
        ) : (
          <span>Analyze Safest Routes</span>
        )}
      </button>
    </form>
  );
};
