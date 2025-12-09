$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Personnel Management System Setup    " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Project Root: $ProjectRoot"
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

function Install-Chocolatey {
    if (-not (Test-Command choco)) {
        Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "Chocolatey installed successfully!" -ForegroundColor Green
    }
}

Write-Host "Step 1: Checking Node.js..." -ForegroundColor Green
if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "  Node.js is installed: $nodeVersion"
} else {
    Write-Host "  Node.js not found. Installing..." -ForegroundColor Yellow
    
    if (-not $isAdmin) {
        Write-Host "  Please run this script as Administrator to install Node.js, or install it manually from https://nodejs.org" -ForegroundColor Red
        Write-Host "  After installing Node.js, run this script again." -ForegroundColor Red
        exit 1
    }
    
    Install-Chocolatey
    choco install nodejs-lts -y
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  Node.js installed successfully!" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 2: Checking npm..." -ForegroundColor Green
if (Test-Command npm) {
    $npmVersion = npm --version
    Write-Host "  npm is installed: v$npmVersion"
} else {
    Write-Host "  npm not found. It should come with Node.js. Please reinstall Node.js." -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "Step 3: Checking pnpm..." -ForegroundColor Green
if (Test-Command pnpm) {
    $pnpmVersion = pnpm --version
    Write-Host "  pnpm is installed: v$pnpmVersion"
} else {
    Write-Host "  pnpm not found. Installing..." -ForegroundColor Yellow
    npm install -g pnpm
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  pnpm installed successfully!" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 4: Checking Python3..." -ForegroundColor Green
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "  Python is installed: $pythonVersion"
} else {
    Write-Host "  Python not found. Installing..." -ForegroundColor Yellow
    
    if (-not $isAdmin) {
        Write-Host "  Please run this script as Administrator to install Python, or install it manually from https://python.org" -ForegroundColor Red
        Write-Host "  Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
        Write-Host "  After installing Python, run this script again." -ForegroundColor Red
        exit 1
    }
    
    Install-Chocolatey
    choco install python -y
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  Python installed successfully!" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 5: Creating Python virtual environment..." -ForegroundColor Green
$BackendPath = Join-Path $ProjectRoot "apps\backend"
Push-Location $BackendPath

if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "  Virtual environment created!" -ForegroundColor Green
}
Write-Host ""
Write-Host "Step 6: Installing Python packages..." -ForegroundColor Green

& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host "  Python packages installed!" -ForegroundColor Green
Write-Host ""

Write-Host "Step 7: Checking .env configuration..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  .env file created from .env.example. Please update with your database credentials." -ForegroundColor Yellow
    } else {
        Write-Host "  .env.example not found! Please create .env file manually." -ForegroundColor Red
    }
} else {
    Write-Host "  .env file exists." -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 8: Initializing database..." -ForegroundColor Green
if ($env:SKIP_DB_INIT -eq "1") {
    Write-Host "  SKIP_DB_INIT=1 set; skipping DB init/seed." -ForegroundColor Yellow
} else {
    Write-Host "  Checking remote database for existing schema..." -ForegroundColor Yellow
    $check = & python -c "from utils.db import check_schema_exists; print('EXISTS' if check_schema_exists() else 'MISSING')" 2>$null
    if ($check -eq "EXISTS") {
        Write-Host "  Database already initialized; skipping init/seed." -ForegroundColor Yellow
    } else {
        Write-Host "  No existing schema detected; creating tables and seeding." -ForegroundColor Green
        python -c "from utils.db import init_db, seed_db; init_db(); seed_db(); print('Database initialized!')"
    }
}
Write-Host ""
deactivate

Pop-Location

Write-Host "Step 9: Installing Node.js dependencies..." -ForegroundColor Green
Push-Location $ProjectRoot
pnpm install
Pop-Location
Write-Host "  Node.js dependencies installed!" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!                      " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application, run:"
Write-Host "  pnpm dev" -ForegroundColor Yellow
Write-Host ""
Write-Host "Default admin credentials:"
Write-Host "  Username: admin" -ForegroundColor Yellow
Write-Host "  Password: admin123" -ForegroundColor Yellow
Write-Host ""
