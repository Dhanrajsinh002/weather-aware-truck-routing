import { describe, it, expect } from 'vitest';
import {
  clampSliderHour,
  nextSliderHour,
  prevSliderHour,
  formatSliderTimeLabel,
  MAX_SLIDER_HOUR,
} from '../features/heatmap/sliderLogic';

describe('slider logic', () => {
  it('clamps slider hours within valid bounds (0 to 48)', () => {
    expect(clampSliderHour(-10)).toBe(0);
    expect(clampSliderHour(50)).toBe(48);
    expect(clampSliderHour(24)).toBe(24);
    expect(clampSliderHour(NaN)).toBe(0);
  });

  it('increments slider hour and loops when loop=true', () => {
    expect(nextSliderHour(0, MAX_SLIDER_HOUR, true)).toBe(1);
    expect(nextSliderHour(23, MAX_SLIDER_HOUR, true)).toBe(24);
    expect(nextSliderHour(48, MAX_SLIDER_HOUR, true)).toBe(0); // Loops back
  });

  it('increments slider hour and stops at max when loop=false', () => {
    expect(nextSliderHour(47, MAX_SLIDER_HOUR, false)).toBe(48);
    expect(nextSliderHour(48, MAX_SLIDER_HOUR, false)).toBe(48); // Stops
  });

  it('decrements slider hour and stops at min (0)', () => {
    expect(prevSliderHour(5)).toBe(4);
    expect(prevSliderHour(1)).toBe(0);
    expect(prevSliderHour(0)).toBe(0);
  });

  it('formats slider offset and local time label correctly', () => {
    const startIso = '2026-10-12T14:00:00.000Z';
    const at0 = formatSliderTimeLabel(startIso, 0);
    expect(at0.offsetLabel).toBe('Departure (T+0h)');
    expect(at0.localTimeLabel).toBeDefined();

    const at24 = formatSliderTimeLabel(startIso, 24);
    expect(at24.offsetLabel).toBe('T+24h');
    expect(at24.localTimeLabel).toBeDefined();
  });
});
