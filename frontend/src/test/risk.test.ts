import { describe, it, expect } from 'vitest';
import {
  getRiskColor,
  getRiskBgColor,
  getRiskScore,
  getRiskLevelFromScore,
  formatRiskLabel,
  RISK_COLORS,
} from '../lib/risk';
import { RiskLevel } from '../types/api';

describe('risk-color helpers', () => {
  it('returns appropriate hex color for string RiskLevels', () => {
    expect(getRiskColor('LOW')).toBe(RISK_COLORS.LOW);
    expect(getRiskColor('MODERATE')).toBe(RISK_COLORS.MODERATE);
    expect(getRiskColor('HIGH')).toBe(RISK_COLORS.HIGH);
    expect(getRiskColor('SEVERE')).toBe(RISK_COLORS.SEVERE);
    expect(getRiskColor('NO_TRAVEL')).toBe(RISK_COLORS.NO_TRAVEL);
  });

  it('maps numeric scores (0-4) to corresponding risk colors', () => {
    expect(getRiskColor(0)).toBe(RISK_COLORS.LOW);
    expect(getRiskColor(1)).toBe(RISK_COLORS.MODERATE);
    expect(getRiskColor(2)).toBe(RISK_COLORS.HIGH);
    expect(getRiskColor(3)).toBe(RISK_COLORS.SEVERE);
    expect(getRiskColor(4)).toBe(RISK_COLORS.NO_TRAVEL);
  });

  it('clamps out-of-range numeric scores safely', () => {
    expect(getRiskColor(-5)).toBe(RISK_COLORS.LOW);
    expect(getRiskColor(10)).toBe(RISK_COLORS.NO_TRAVEL);
    expect(getRiskColor(2.3)).toBe(RISK_COLORS.HIGH);
  });

  it('returns valid background colors for badges and alerts', () => {
    const levels: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'SEVERE', 'NO_TRAVEL'];
    levels.forEach((lvl) => {
      const bg = getRiskBgColor(lvl);
      expect(bg).toContain('rgba');
    });
  });

  it('correctly maps scores to levels and levels to scores', () => {
    expect(getRiskScore('LOW')).toBe(0);
    expect(getRiskScore('SEVERE')).toBe(3);
    expect(getRiskScore('NO_TRAVEL')).toBe(4);

    expect(getRiskLevelFromScore(0)).toBe('LOW');
    expect(getRiskLevelFromScore(1)).toBe('MODERATE');
    expect(getRiskLevelFromScore(3)).toBe('SEVERE');
    expect(getRiskLevelFromScore(4)).toBe('NO_TRAVEL');
  });

  it('formats user-friendly labels', () => {
    expect(formatRiskLabel('LOW')).toBe('Low');
    expect(formatRiskLabel('MODERATE')).toBe('Moderate');
    expect(formatRiskLabel('HIGH')).toBe('High');
    expect(formatRiskLabel('SEVERE')).toBe('Severe');
    expect(formatRiskLabel('NO_TRAVEL')).toBe('No Travel');
  });
});
