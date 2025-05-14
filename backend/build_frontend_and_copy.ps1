# PowerShell script to build React frontend and copy build output to Flask backend

# Go to the frontend directory
Push-Location ../frontend

# Run the React build
npm install
npm run build

# Return to backend directory
Pop-Location

# Install the backend package in development mode
pip install -e .

# Ensure static and templates directories exist
if (!(Test-Path "./static")) { New-Item -ItemType Directory -Path "./static" }
if (!(Test-Path "./templates")) { New-Item -ItemType Directory -Path "./templates" }

# Copy index.html to templates
Copy-Item -Path "../frontend/dist/index.html" -Destination "./templates/index.html" -Force

# Copy all other files and folders to static
Copy-Item -Path "../frontend/dist/*" -Destination "./static/" -Recurse -Force

Write-Host "React build files copied to Flask backend." 