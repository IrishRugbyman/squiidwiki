# PowerShell script to build the TypeScript project
# This script handles setting up PATH correctly before running npm commands

# Function to add Node.js to PATH permanently if it doesn't exist
function Add-NodeJsToPath {
    $nodePath = "C:\Program Files\nodejs"
    $currentPath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    
    if (-not $currentPath.Contains($nodePath)) {
        Write-Host "Node.js not found in PATH. Adding it now..." -ForegroundColor Yellow
        try {
            # Add to current session
            $env:Path += ";$nodePath"
            
            # Add permanently (requires admin privileges)
            if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
                [Environment]::SetEnvironmentVariable('Path', $currentPath + ";$nodePath", 'Machine')
                Write-Host "Node.js added to system PATH permanently." -ForegroundColor Green
            } else {
                Write-Host "Warning: Admin privileges required to add Node.js to PATH permanently." -ForegroundColor Yellow
                Write-Host "Node.js added to PATH for current session only." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Error updating PATH: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Node.js already in PATH" -ForegroundColor Green
    }
}

# Add Node.js to PATH
Add-NodeJsToPath

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "Using Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js not found. Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check if the js directory exists, create it if not
if (-not (Test-Path -Path "frontend/static/js")) {
    New-Item -ItemType Directory -Path "frontend/static/js" -Force
    Write-Host "Created output directory: frontend/static/js" -ForegroundColor Green
}

# Run the build process
Write-Host "Building TypeScript project..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully. Output saved to frontend/static/js/app.js" -ForegroundColor Green
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
} 