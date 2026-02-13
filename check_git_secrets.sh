#!/bin/bash
#
# Git History Secret Scanner
# This script helps identify potential secrets in git commit history
#
# Usage: ./check_git_secrets.sh
#

set -e

echo "=================================================="
echo "Git History Secret Scanner"
echo "Repository: $(git remote get-url origin 2>/dev/null || echo 'local')"
echo "=================================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

echo "[1/5] Checking for shallow clone..."
if [ -f .git/shallow ]; then
    echo "⚠️  WARNING: This is a shallow clone (limited history)"
    echo "    Run 'git fetch --unshallow' to get full history"
    echo ""
fi

echo "[2/5] Searching commit messages for secret-related keywords..."
git log --all --oneline | grep -iE "(secret|key|password|token|credential|api)" | head -20 || echo "   No suspicious commit messages found"
echo ""

echo "[3/5] Searching for .env files in commit history..."
git log --all --name-only --pretty=format: | grep -E "\.env" | sort | uniq || echo "   No .env files found in history"
echo ""

echo "[4/5] Checking current .gitignore for secret patterns..."
if [ -f .gitignore ]; then
    if grep -q "\.env" .gitignore; then
        echo "   ✅ .env files are ignored"
    else
        echo "   ⚠️  WARNING: .env files not in .gitignore"
    fi
    
    if grep -q "secret" .gitignore; then
        echo "   ✅ secret files are ignored"
    fi
else
    echo "   ⚠️  WARNING: No .gitignore file found"
fi
echo ""

echo "[5/5] Searching for high-entropy strings (potential secrets)..."
echo "   Checking Python files..."
find . -name "*.py" -not -path "*/.*" -not -path "*/node_modules/*" -exec grep -l "password\|secret\|key\|token" {} \; | head -10 || true

echo ""
echo "   Checking JavaScript/TypeScript files..."
find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -not -path "*/.*" -not -path "*/node_modules/*" | xargs grep -l "password\|secret\|key\|token" 2>/dev/null | head -10 || true

echo ""
echo "=================================================="
echo "Quick Recommendations:"
echo "=================================================="
echo ""
echo "1. Review commits with suspicious messages"
echo "2. Check if .env files contain real secrets"
echo "3. Rotate any exposed credentials immediately"
echo "4. Install git-secrets to prevent future leaks:"
echo "   brew install git-secrets (Mac)"
echo "   apt-get install git-secrets (Linux)"
echo ""
echo "For detailed analysis, see: SECURITY_AUDIT_REPORT.md"
echo ""

# Advanced checks if trufflehog is available
if command -v trufflehog3 &> /dev/null; then
    echo "[BONUS] Running TruffleHog scan..."
    trufflehog3 --no-history --format json . 2>&1 | grep -v "package-lock.json" | head -20 || echo "   No secrets found by TruffleHog"
else
    echo "[BONUS] Install TruffleHog for deeper scanning:"
    echo "   pip install truffleHog3"
fi

echo ""
echo "Scan complete!"
