import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import './AccordionReport.css'; // We'll create CSS next

const AccordionReport = ({ title, summary, children, icon }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`accordion-report ${isOpen ? 'open' : ''}`}>
      <button className="accordion-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="header-content">
          {icon && <FontAwesomeIcon icon={icon} className="header-icon" />}
          <span className="header-title">{title}</span>
          {summary && !isOpen && <span className="header-summary">{summary}</span>}
        </div>
        <FontAwesomeIcon icon={isOpen ? faChevronUp : faChevronDown} className="chevron-icon" />
      </button>
      {isOpen && (
        <div className="accordion-content">
          {children}
        </div>
      )}
    </div>
  );
};

export default AccordionReport;
