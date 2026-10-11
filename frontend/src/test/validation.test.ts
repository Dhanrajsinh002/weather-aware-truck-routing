import { describe, it, expect } from 'vitest';
import { validateTripForm, FormState, isValidForm } from '../features/planner/validation';
import { toInputDateTimeString } from '../lib/format';

describe('form validation', () => {
  const baseTime = new Date('2026-10-12T12:00:00Z');

  const validForm: FormState = {
    origin: { label: 'Chicago, IL', lat: 41.8781, lng: -87.6298 },
    originQuery: 'Chicago, IL',
    destination: { label: 'Denver, CO', lat: 39.7392, lng: -104.9903 },
    destinationQuery: 'Denver, CO',
    departureTimeLocal: toInputDateTimeString(new Date('2026-10-12T14:00:00Z')),
    loadWeightLb: 42000,
    interval: 'auto',
  };

  it('passes validation on a valid form', () => {
    const errors = validateTripForm(validForm, baseTime);
    expect(isValidForm(errors)).toBe(true);
    expect(errors).toEqual({});
  });

  it('requires origin', () => {
    const form: FormState = {
      ...validForm,
      origin: null,
      originQuery: '',
    };
    const errors = validateTripForm(form, baseTime);
    expect(errors.origin).toBeDefined();
    expect(errors.origin).toContain('Origin location is required');
  });

  it('requires destination', () => {
    const form: FormState = {
      ...validForm,
      destination: null,
      destinationQuery: '',
    };
    const errors = validateTripForm(form, baseTime);
    expect(errors.destination).toBeDefined();
    expect(errors.destination).toContain('Destination location is required');
  });

  it('rejects identical origin and destination', () => {
    const formWithSameCoords: FormState = {
      ...validForm,
      destination: { ...validForm.origin! },
      destinationQuery: validForm.originQuery,
    };
    const errors = validateTripForm(formWithSameCoords, baseTime);
    expect(errors.destination).toBeDefined();
    expect(errors.destination).toContain('cannot be the same');
  });

  it('rejects departures more than 1 hour in the past', () => {
    const twoHoursAgo = new Date(baseTime.getTime() - 2 * 60 * 60 * 1000);
    const form: FormState = {
      ...validForm,
      departureTimeLocal: toInputDateTimeString(twoHoursAgo),
    };
    const errors = validateTripForm(form, baseTime);
    expect(errors.departureTime).toBeDefined();
    expect(errors.departureTime).toContain('1 hour in the past');
  });

  it('rejects departures more than 14 days in the future', () => {
    const fifteenDaysAhead = new Date(baseTime.getTime() + 15 * 24 * 60 * 60 * 1000);
    const form: FormState = {
      ...validForm,
      departureTimeLocal: toInputDateTimeString(fifteenDaysAhead),
    };
    const errors = validateTripForm(form, baseTime);
    expect(errors.departureTime).toBeDefined();
    expect(errors.departureTime).toContain('14 days ahead');
  });

  it('validates load weight boundaries (1 to 100,000 lb)', () => {
    // 0 lb
    let errors = validateTripForm({ ...validForm, loadWeightLb: 0 }, baseTime);
    expect(errors.loadWeight).toBeDefined();
    expect(errors.loadWeight).toContain('at least 1 lb');

    // Negative
    errors = validateTripForm({ ...validForm, loadWeightLb: -500 }, baseTime);
    expect(errors.loadWeight).toBeDefined();

    // Over 100,000 lb
    errors = validateTripForm({ ...validForm, loadWeightLb: 100001 }, baseTime);
    expect(errors.loadWeight).toBeDefined();
    expect(errors.loadWeight).toContain('100,000 lb');

    // Valid boundaries
    errors = validateTripForm({ ...validForm, loadWeightLb: 1 }, baseTime);
    expect(errors.loadWeight).toBeUndefined();

    errors = validateTripForm({ ...validForm, loadWeightLb: 100000 }, baseTime);
    expect(errors.loadWeight).toBeUndefined();
  });
});
