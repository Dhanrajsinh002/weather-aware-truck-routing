export function formatDistance(miles: number): string {
  return `${miles.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours === 0) {
    return `${minutes}m`;
  }
  return `${hours}h ${minutes.toString().padStart(2, '0')}m`;
}

export function formatWeight(lbs: number): string {
  return `${lbs.toLocaleString()} lb`;
}

export function formatLocalTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString;
  }
}

export function formatLocalDateTime(date: Date): string {
  return date.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function getOffsetLocalTime(startTimeIso: string, offsetHours: number): string {
  try {
    const d = new Date(startTimeIso);
    if (isNaN(d.getTime())) return `+${offsetHours}h`;
    d.setHours(d.getHours() + offsetHours);
    return formatLocalTime(d.toISOString());
  } catch {
    return `+${offsetHours}h`;
  }
}

export function toInputDateTimeString(date: Date): string {
  // Returns YYYY-MM-DDTHH:mm format in local time for datetime-local input
  const pad = (n: number) => n.toString().padStart(2, '0');
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const min = pad(date.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
}
