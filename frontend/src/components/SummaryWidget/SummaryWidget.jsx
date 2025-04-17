import React from 'react';
import './SummaryWidget.css';

const SummaryWidget = ({ summary, isLoading }) => {
  return (
    <div className="summary-widget-container">
      <h4>AI Summary (Illustrative)</h4>
      <div className="summary-content">
        {isLoading ? (
          <p>Loading summary...</p>
        ) : summary ? (
          <p>{summary}</p>
        ) : (
          <p>No data available to generate summary.</p>
        )}
      </div>
    </div>
  );
};

export default SummaryWidget; 