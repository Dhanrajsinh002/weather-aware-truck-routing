import { RiskLevel, RISK_NUMERIC_MAP, NUMERIC_TO_RISK_MAP } from '../types/api';

export const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: '#10b981', // Emerald / Green
  MODERATE: '#eab308', // Amber / Yellow
  HIGH: '#f97316', // Orange
  SEVERE: '#ef4444', // Red
  NO_TRAVEL: '#881337', // Deep Maroon / Dark Red
};

export const RISK_BG_COLORS: Record<RiskLevel, string> = {
  LOW: 'rgba(16, 185, 129, 0.15)',
  MODERATE: 'rgba(234, 179, 8, 0.15)',
  HIGH: 'rgba(249, 115, 22, 0.18)',
  SEVERE: 'rgba(239, 68, 68, 0.20)',
  NO_TRAVEL: 'rgba(136, 19, 55, 0.28)',
};

export const RISK_BORDER_COLORS: Record<RiskLevel, string> = {
  LOW: 'rgba(16, 185, 129, 0.4)',
  MODERATE: 'rgba(234, 179, 8, 0.4)',
  HIGH: 'rgba(249, 115, 22, 0.5)',
  SEVERE: 'rgba(239, 68, 68, 0.6)',
  NO_TRAVEL: 'rgba(136, 19, 55, 0.8)',
};

export const RISK_DESCRIPTIONS: Record<RiskLevel, string> = {
  LOW: 'Normal driving conditions. Minimal weather impact.',
  MODERATE: 'Minor hazards. Reduced speeds and caution advised.',
  HIGH: 'Challenging conditions. High crosswinds or moderate precipitation.',
  SEVERE: 'Dangerous conditions. High risk for heavy loads and high-profile trucks.',
  NO_TRAVEL: 'Extreme hazard. Travel prohibited or unsafe.',
};

export function getRiskColor(level: RiskLevel | number): string {
  if (typeof level === 'number') {
    const clamped = Math.max(0, Math.min(4, Math.round(level)));
    const riskLevel = NUMERIC_TO_RISK_MAP[clamped] || 'LOW';
    return RISK_COLORS[riskLevel];
  }
  return RISK_COLORS[level] || RISK_COLORS.LOW;
}

export function getRiskBgColor(level: RiskLevel): string {
  return RISK_BG_COLORS[level] || RISK_BG_COLORS.LOW;
}

export function getRiskBorderColor(level: RiskLevel): string {
  return RISK_BORDER_COLORS[level] || RISK_BORDER_COLORS.LOW;
}

export function getRiskScore(level: RiskLevel): number {
  return RISK_NUMERIC_MAP[level] ?? 0;
}

export function getRiskLevelFromScore(score: number): RiskLevel {
  const clamped = Math.max(0, Math.min(4, Math.round(score)));
  return NUMERIC_TO_RISK_MAP[clamped] || 'LOW';
}

export function formatRiskLabel(level: RiskLevel): string {
  switch (level) {
    case 'NO_TRAVEL':
      return 'No Travel';
    case 'SEVERE':
      return 'Severe';
    case 'HIGH':
      return 'High';
    case 'MODERATE':
      return 'Moderate';
    case 'LOW':
      return 'Low';
    default:
      return level;
  }
}
