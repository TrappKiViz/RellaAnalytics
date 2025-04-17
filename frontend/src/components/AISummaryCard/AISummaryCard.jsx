import React from 'react';
import './AISummaryCard.css'; // We'll create this CSS file next
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBrain } from '@fortawesome/free-solid-svg-icons'; // Example icon

const AISummaryCard = ({ title = "AI Analysis", summary, isLoading }) => {
  return (
    <div className="ai-summary-card">
      <h3 className="ai-summary-title">
        <FontAwesomeIcon icon={faBrain} className="ai-summary-icon" />
        {title}
      </h3>
      <div className="ai-summary-content">
        {isLoading ? (
          <p>Generating summary...</p>
        ) : (
          <p>{summary || "No summary available."}</p>
        )}
      </div>
    </div>
  );
};

export default AISummaryCard;
