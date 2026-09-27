import React from "react";

export default function RiskBox({ risk }) {
  const level = String(
    risk?.level ??
    risk?.risk_level ??
    "LOW"
  ).toUpperCase();

  const score = Number(
    risk?.score ??
    risk?.risk_score ??
    0
  );

  const reason =
    risk?.reason ??
    risk?.primary_reason ??
    (Array.isArray(risk?.reasons) && risk.reasons.length > 0
      ? risk.reasons.join(" • ")
      : null);

  return (
    <div className={`risk-box risk-${level.toLowerCase()}`}>
      <div className="risk-box-title">
        RISK
      </div>

      <div className="risk-box-level">
        {level}
      </div>

      <div className="risk-box-score">
        SCORE: {score}
      </div>

      {reason && (
        <div className="risk-box-reason">
          {reason}
        </div>
      )}
    </div>
  );
}
