# Technical Context: Rella Analytics Platform

## 1. Technologies

*   **Backend:** Python
    *   Framework: Flask (chosen for lightweight API development)
*   **Frontend:** JavaScript
    *   Framework: React (chosen for component model and popularity)
*   **Database:** PostgreSQL (chosen for robustness, relational data, and geospatial capabilities)
*   **Data Science / ML Libraries:**
    *   Pandas (Data manipulation and analysis)
    *   Scikit-learn (General machine learning algorithms)
    *   Statsmodels (Statistical modeling, time series analysis)
    *   Prophet (Facebook's time series forecasting library)
*   **Containerization:** Docker

## 2. Development Setup

*   (To be defined - e.g., Python version, Node.js version, package managers pip/npm, virtual environment strategy, linting/formatting tools)

## 3. Technical Constraints

*   Must be deployable via Docker containers.
*   Designed for cloud deployment (AWS/GCP/Azure - specific provider TBD).
*   Architecture should support multi-tenancy for the future SaaS model.

## 4. Dependencies

*   Requires Python environment.
*   Requires Node.js environment for frontend development.
*   Requires PostgreSQL database instance.
*   Requires Docker engine. 