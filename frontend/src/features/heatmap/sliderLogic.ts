import { formatLocalTime } from '../../lib/format';

export const MIN_SLIDER_HOUR = 0;
export const MAX_SLIDER_HOUR = 48;

export function clampSliderHour(
  hour: number,
  min: number = MIN_SLIDER_HOUR,
  max: number = MAX_SLIDER_HOUR
): number {
  if (isNaN(hour)) return min;
  return Math.max(min, Math.min(max, Math.round(hour)));
}

export function nextSliderHour(
  current: number,
  max: number = MAX_SLIDER_HOUR,
  loop: boolean = true
): number {
  if (current >= max) {
    return loop ? MIN_SLIDER_HOUR : max;
  }
  return current + 1;
}

export function prevSliderHour(
  current: number,
  min: number = MIN_SLIDER_HOUR
): number {
  if (current <= min) {
    return min;
  }
  return current - 1;
}

export function getForecastDate(startTimeIso: string, hourOffset: number): Date {
  const base = new Date(startTimeIso);
  if (isNaN(base.getTime())) return new Date();
  const target = new Date(base.getTime());
  target.setHours(target.getHours() + hourOffset);
  return target;
}

export function formatSliderTimeLabel(startTimeIso: string, hourOffset: number): {
  offsetLabel: string;
  localTimeLabel: string;
} {
  const date = getForecastDate(startTimeIso, hourOffset);
  return {
    offsetLabel: hourOffset === 0 ? 'Departure (T+0h)' : `T+${hourOffset}h`,
    localTimeLabel: formatLocalTime(date.toISOString()),
  };
}
