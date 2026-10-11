import React from 'react';
import { useTripContext } from '../../context/TripContext';
import { CheckCircle2, AlertTriangle, Award, Info } from 'lucide-react';

export const RecommendationBanner: React.FC = () => {
  const { tripData } = useTripContext();

  if (!tripData || !tripData.recommendation) {
    return null;
  }

  const { recommendation, routes } = tripData;
  const recommendedRoute = routes.find((r) => r.id === recommendation.route_id) || routes[0];

  return (
    <div className="recommendation-panel">
      <div className="rec-header">
        <div className="rec-badge">
          <Award size={18} />
          <span>Optimal Route Recommendation</span>
        </div>
        {recommendedRoute && (
          <h3 className="rec-title">
            Recommended: <span className="rec-highlight">{recommendedRoute.label}</span>
          </h3>
        )}
      </div>

      {recommendation.reasons && recommendation.reasons.length > 0 && (
        <div className="rec-reasons-container">
          <h4 className="rec-subhead">Decision Factors</h4>
          <ul className="rec-reasons-list">
            {recommendation.reasons.map((reason, idx) => (
              <li key={idx} className="rec-reason-item">
                <CheckCircle2 size={16} className="rec-icon-check" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendation.warnings && recommendation.warnings.length > 0 && (
        <div className="rec-warnings-container">
          <div className="warning-box">
            <AlertTriangle size={18} className="warning-icon" />
            <div className="warning-content">
              <h5 className="warning-heading">Corridor Weather Warnings</h5>
              <ul className="warning-list">
                {recommendation.warnings.map((warn, idx) => (
                  <li key={idx}>{warn}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {(!recommendation.warnings || recommendation.warnings.length === 0) && (
        <div className="rec-clear-note">
          <Info size={14} />
          <span>All alternative routes analyzed against wind thresholds and gross truck weight limits.</span>
        </div>
      )}
    </div>
  );
};
