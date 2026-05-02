# install_skills.ps1 - Idempotent installer for obra/superpowers skills
param(
    [switch]$Force,
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ToolsDir = Join-Path $RepoRoot "tools"
$SuperpowersDir = Join-Path $ToolsDir "superpowers"
$SkillsDest = Join-Path $RepoRoot ".opencode" "skills"
$UpstreamUrl = "https://github.com/obra/superpowers.git"

$RequiredSkills = @(
    "using-superpowers", "brainstorming", "writing-plans",
    "executing-plans", "test-driven-development", "requesting-code-review",
    "receiving-code-review", "verification-before-completion",
    "using-git-worktrees", "finishing-a-development-branch",
    "subagent-driven-development", "dispatching-parallel-agents",
    "systematic-debugging"
)

Write-Host "=== Superpowers Skills Installer ===" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
New-Item -ItemType Directory -Force -Path $SkillsDest | Out-Null

if (Test-Path (Join-Path $SuperpowersDir ".git")) {
    Write-Host "[SKIP] superpowers repo exists" -ForegroundColor Yellow
    if ($Force) {
        Write-Host "[UPDATE] Fetching latest..." -ForegroundColor Green
        git -C $SuperpowersDir fetch origin $Branch
        git -C $SuperpowersDir checkout $Branch
        git -C $SuperpowersDir reset --hard origin/$Branch
    }
} else {
    Write-Host "[CLONE] Cloning obra/superpowers..." -ForegroundColor Green
    git clone --depth 1 --branch $Branch $UpstreamUrl $SuperpowersDir
}

$Installed = 0
$Skipped = 0

foreach ($Skill in $RequiredSkills) {
    $SourceSkillMd = Join-Path $SuperpowersDir "skills" $Skill "SKILL.md"
    $DestDir = Join-Path $SkillsDest $Skill

    if (-not (Test-Path $SourceSkillMd)) {
        Write-Host "[WARN] Skill '$Skill' not found upstream" -ForegroundColor Red
        continue
    }

    if ((Test-Path (Join-Path $DestDir "SKILL.md")) -and (-not $Force)) {
        Write-Host "[SKIP] $Skill" -ForegroundColor Yellow
        $Skipped++
        continue
    }

    Write-Host "[INSTALL] $Skill" -ForegroundColor Green
    if (Test-Path $DestDir) { Remove-Item -Recurse -Force $DestDir }
    Copy-Item -Recurse -Force (Join-Path $SuperpowersDir "skills" $Skill) $DestDir
    $Installed++
}

Write-Host ""
Write-Host "=== Done: $Installed installed, $Skipped skipped ===" -ForegroundColor Cyan
Write-Host "Skills at: $SkillsDest"
Write-Host "Verify: ask agent 'Tell me about your superpowers'"
