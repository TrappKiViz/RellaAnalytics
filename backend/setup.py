from setuptools import setup, find_packages

setup(
    name="rella-analytics-backend",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask>=2.0',
        'Flask-Cors>=3.0',
        'python-dotenv>=1.0',
        'Werkzeug>=2.0',
        'click>=8.0',
        'Flask-Caching',
        'Flask-Login>=0.6',
        'pandas>=1.3',
        'statsmodels>=0.13',
        'patsy>=0.5',
        'prophet>=1.0',
        'plotly>=5.0',
        'requests>=2.20',
        'gunicorn'
    ],
) 