#!/bin/bash
set -e

# Build the frontend
cd frontend
npm install
npm run build

# Copy built files to backend/static and backend/templates
cd ..
rm -rf backend/static/*
rm -rf backend/templates/*
cp -r frontend/dist/* backend/static/
cp -r frontend/public/* backend/static/ 2>/dev/null || true
cp -r frontend/templates/* backend/templates/ 2>/dev/null || true 