# Build release packages (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File deploy/scripts/build-release.ps1
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '../..')
$Out = Join-Path $Root 'deploy/release'
$EnvFile = Join-Path $Root 'deploy/env/frontend-build.env'

New-Item -ItemType Directory -Force -Path $Out | Out-Null
Get-ChildItem $Out -Filter '*.tar.gz' -ErrorAction SilentlyContinue | Remove-Item -Force

$AdminDomain = 'http://localhost:5173'
$SellerDomain = 'http://localhost:5175'
$CustomerDomain = 'http://localhost:5174'
$BaiduAk = ''

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            switch ($name) {
                'ADMIN_DOMAIN' { $AdminDomain = $value }
                'SELLER_DOMAIN' { $SellerDomain = $value }
                'CUSTOMER_DOMAIN' { $CustomerDomain = $value }
                'VITE_BAIDU_MAP_AK' { $BaiduAk = $value }
            }
        }
    }
} else {
    Write-Host "[warn] Missing $EnvFile, using default domains" -ForegroundColor Yellow
}

$env:VITE_API_BASE_URL = '/api'
# Media must load from the current site origin (/media/ proxied by Nginx), not backend host.
Remove-Item Env:VITE_API_ORIGIN -ErrorAction SilentlyContinue
$env:VITE_API_ORIGIN = ''
# Drop mistaken Windows drive paths from env (axios "Unsupported protocol D:" errors)
foreach ($name in @('VITE_API_ORIGIN', 'VITE_WS_URL', 'VITE_API_BASE_URL')) {
    $val = [Environment]::GetEnvironmentVariable($name, 'Process')
    if (-not $val) {
        $val = [Environment]::GetEnvironmentVariable($name, 'User')
    }
    if ($val -and ($val -match '^[A-Za-z]:')) {
        Write-Host "[warn] Ignoring invalid $name (Windows path): $val" -ForegroundColor Yellow
        Remove-Item -Path "env:$name" -ErrorAction SilentlyContinue
        if ($name -eq 'VITE_API_BASE_URL') {
            $env:VITE_API_BASE_URL = '/api'
        }
    }
}

function Test-NpmExit {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "npm failed: $Step (exit $LASTEXITCODE)"
    }
}

function Ensure-Dependencies {
    param([string]$Dir)
    $viteCmd = Join-Path $Dir 'node_modules/.bin/vite.cmd'
    $viteBin = Join-Path $Dir 'node_modules/.bin/vite'
    if ((Test-Path $viteCmd) -or (Test-Path $viteBin)) {
        Write-Host '  deps OK, skip npm install' -ForegroundColor DarkGray
        return
    }
    Write-Host '  npm install ...' -ForegroundColor DarkGray
    Push-Location $Dir
    try {
        npm install
        Test-NpmExit 'npm install'
    } finally {
        Pop-Location
    }
}

function Build-App {
    param(
        [string]$Name,
        [string]$Dir,
        [hashtable]$ExtraEnv = @{}
    )
    Write-Host "==> Building $Name ..." -ForegroundColor Cyan
    Ensure-Dependencies -Dir $Dir
    Push-Location $Dir
    try {
        foreach ($key in $ExtraEnv.Keys) {
            Set-Item -Path "env:$key" -Value $ExtraEnv[$key]
        }
        npm run build
        Test-NpmExit "npm run build ($Name)"
    } finally {
        Pop-Location
    }
    $distIndex = Join-Path $Dir 'dist/index.html'
    if (-not (Test-Path $distIndex)) {
        throw "Build failed: missing $distIndex"
    }
}

Build-App -Name 'admin' -Dir (Join-Path $Root 'admin')
Build-App -Name 'seller' -Dir (Join-Path $Root 'seller')
Build-App -Name 'customer' -Dir (Join-Path $Root 'customer') -ExtraEnv @{
    VITE_SELLER_URL = $SellerDomain
    VITE_BAIDU_MAP_AK = $BaiduAk
}

Write-Host '==> Packing frontend dist ...' -ForegroundColor Cyan
tar -czf (Join-Path $Out 'adminDist.tar.gz') -C (Join-Path $Root 'admin/dist') .
tar -czf (Join-Path $Out 'sellerDist.tar.gz') -C (Join-Path $Root 'seller/dist') .
tar -czf (Join-Path $Out 'customerDist.tar.gz') -C (Join-Path $Root 'customer/dist') .

Write-Host '==> Packing backend adminAPI ...' -ForegroundColor Cyan
Push-Location $Root
try {
    tar -czf (Join-Path $Out 'backend.tar.gz') `
        --exclude='venv' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' `
        --exclude='db.sqlite3' --exclude='.env' --exclude='media' --exclude='staticfiles' `
        adminAPI
    tar -czf (Join-Path $Out 'deploy.tar.gz') `
        --exclude='release' --exclude='env/frontend-build.env' `
        deploy
} finally {
    Pop-Location
}

Write-Host ''
Write-Host "Release packages: $Out" -ForegroundColor Green
Get-ChildItem $Out -Filter '*.tar.gz' | Format-Table Name, Length -AutoSize
Write-Host ''
Write-Host 'Upload to server:'
Write-Host '  scp deploy/release/*.tar.gz root@your-server:/var/www/admin/'
