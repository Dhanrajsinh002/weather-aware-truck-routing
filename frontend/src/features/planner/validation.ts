import { GeocodeLocation, IntervalSelection } from '../../types/api';

export interface FormState {
  origin: GeocodeLocation | null;
  originQuery: string;
  destination: GeocodeLocation | null;
  destinationQuery: string;
  departureTimeLocal: string;
  loadWeightLb: string | number;
  interval: IntervalSelection;
}

export interface ValidationErrors {
  origin?: string;
  destination?: string;
  departureTime?: string;
  loadWeight?: string;
  general?: string;
}

export function validateTripForm(form: FormState, now: Date = new Date()): ValidationErrors {
  const errors: ValidationErrors = {};

  // Origin check
  if (!form.origin && !form.originQuery.trim()) {
    errors.origin = 'Origin location is required.';
  }

  // Destination check
  if (!form.destination && !form.destinationQuery.trim()) {
    errors.destination = 'Destination location is required.';
  }

  // Same origin/destination check
  if (
    form.origin &&
    form.destination &&
    form.origin.lat === form.destination.lat &&
    form.origin.lng === form.destination.lng
  ) {
    errors.destination = 'Origin and destination cannot be the same place.';
  } else if (
    form.originQuery.trim().toLowerCase() === form.destinationQuery.trim().toLowerCase() &&
    form.originQuery.trim().length > 0
  ) {
    errors.destination = 'Origin and destination cannot be the same.';
  }

  // Departure time check
  if (!form.departureTimeLocal) {
    errors.departureTime = 'Departure time is required.';
  } else {
    const depDate = new Date(form.departureTimeLocal);
    if (isNaN(depDate.getTime())) {
      errors.departureTime = 'Invalid departure date/time.';
    } else {
      const diffMs = depDate.getTime() - now.getTime();
      const pastLimitMs = -1 * 60 * 60 * 1000; // 1 hour past
      const futureLimitMs = 14 * 24 * 60 * 60 * 1000; // 14 days ahead

      if (diffMs < pastLimitMs) {
        errors.departureTime = 'Departure time cannot be more than 1 hour in the past.';
      } else if (diffMs > futureLimitMs) {
        errors.departureTime = 'Departure time cannot be more than 14 days ahead (forecast limit).';
      }
    }
  }

  // Load weight check
  const weightNum = typeof form.loadWeightLb === 'string' ? parseFloat(form.loadWeightLb) : form.loadWeightLb;
  if (isNaN(weightNum) || weightNum === null || weightNum === undefined) {
    errors.loadWeight = 'Load weight is required.';
  } else if (weightNum < 1) {
    errors.loadWeight = 'Load weight must be at least 1 lb.';
  } else if (weightNum > 100000) {
    errors.loadWeight = 'Load weight cannot exceed 100,000 lb.';
  }

  return errors;
}

export function isValidForm(errors: ValidationErrors): boolean {
  return Object.keys(errors).length === 0;
}
