# Security Audit Report: Git History Analysis
**Date:** 2026-02-13  
**Repository:** evnmck/cloud-app  
**Total Commits Analyzed:** 34

## Executive Summary

⚠️ **CRITICAL FINDINGS:** Evidence of secrets and API keys committed to the repository history has been identified. While these have been removed from the current working tree, they remain in the git history and should be considered **COMPROMISED**.

## Detailed Findings

### 1. HIGH RISK: .env Files Were Committed (Multiple Occurrences)

**Commits Involved:**
- `e218d6550d399a4cc8776d3610462ad922390de9` (2025-12-23) - "Ignore env files; stop tracking frontend/.env.development"
  - **File Removed:** `frontend/.env.development` (2 lines deleted)
  - **Added:** `frontend/.env.example` with placeholder values
  
- `938d042ee3b9896f7b3da6db5b344ebbeb67e5a7` (2025-12-23) - "rm from history"
  - **File Re-added:** `frontend/.env.development` (2 lines)
  - This suggests an attempt to clean git history that was not fully successful

- `23181d9546d28704dfdfce24b43fbf5d056727a0` (2025-12-23) - "Ignore .env files"
  - Added .env to .gitignore

**Content from .env.example:**
```
VITE_API_BASE_URL=EXAMPLE_BASE_URL
VITE_API_TOKEN=EXAMPLE_TOKEN
```

**Risk:** The actual `.env.development` file that was tracked likely contained real API endpoints and tokens. These values are still accessible in the git history.

### 2. HIGH RISK: API Token Added to Code

**Commit:** `649729a2e3ec3ffb326c80827ee9b0a7e644f701` (2025-11-26) - "add api token"

**Files Modified:**
- `.github/workflows/deploy.yml` (2 changes)
- `backend/api/handler.py` (6 changes)
- `infra/app_stack.py` (3 changes)

**Current Implementation (Good):**
The current code properly uses environment variables:
- `API_TOKEN = os.environ.get("API_TOKEN")` in handler.py
- GitHub Actions uses `${{ secrets.API_TOKEN }}`

**Risk:** The commit message "add api token" suggests a token may have been hardcoded initially and later moved to environment variables in commit `3787eafe060b6590bdc6dbf9df1c1282a87c2c66` ("env variables pulled out").

### 3. MEDIUM RISK: Authentication Key References

**Commit:** `5c043f41513449dbd60cef5474ffb70356a3da23` (2026-02-13) - "only login with correct key"

**Analysis:** This commit implements proper authentication checking in the Login page and API handler. The current implementation is secure (validates against environment variable).

### 4. AWS Credentials in GitHub Secrets

**Current Status:** ✅ GOOD - Properly configured

GitHub Actions workflow uses:
- `${{ secrets.AWS_ACCESS_KEY_ID }}`
- `${{ secrets.AWS_SECRET_ACCESS_KEY }}`
- `${{ secrets.AWS_REGION }}`
- `${{ secrets.ACCOUNT_ID }}`
- `${{ secrets.API_TOKEN }}`

These are properly stored in GitHub Secrets and not in the code.

## Files Currently Protected

✅ Current `.gitignore` properly excludes:
```
.env
.env.*
!.env.example
```

## Security Recommendations

### IMMEDIATE ACTIONS REQUIRED:

1. **ROTATE ALL SECRETS** ⚠️ CRITICAL
   - Rotate the API_TOKEN immediately
   - Review and rotate AWS access keys if they were ever in .env files
   - Any secret that was in `frontend/.env.development` should be considered compromised

2. **Audit Specific Commits**
   Since the repository clone is shallow, recommend manually reviewing these commits on GitHub:
   - Review commit `649729a2e3ec3ffb326c80827ee9b0a7e644f701` for hardcoded tokens
   - Check if `frontend/.env.development` from commit `938d042e` or earlier contained real secrets
   - View commits at: `https://github.com/evnmck/cloud-app/commit/<SHA>`

3. **Consider Git History Rewrite** (Advanced)
   - Use `git filter-branch` or `BFG Repo-Cleaner` to permanently remove secrets from git history
   - Note: This requires force-pushing and coordinating with all users
   - Alternatively: Consider the current repository compromised and migrate to a new repository

4. **Enable GitHub Secret Scanning**
   - Enable GitHub Advanced Security features if available
   - This will automatically detect secrets committed to the repository

5. **Implement Pre-commit Hooks**
   - Install git-secrets or similar tool: `brew install git-secrets` (Mac) or equivalent
   - Configure to prevent accidental secret commits

### PREVENTIVE MEASURES:

1. **Add .env.example Files**
   - ✅ Already done for frontend
   - Consider adding for backend and infra directories

2. **Use Environment Variables Everywhere**
   - ✅ Current code properly uses `os.environ.get()`
   - ✅ GitHub Actions uses secrets properly

3. **Code Review Process**
   - Ensure all PRs are reviewed for sensitive data before merging
   - Use automated tools in CI/CD to scan for secrets

4. **Documentation**
   - Document which secrets are needed for development
   - Provide instructions for obtaining development credentials

## Timeline of Security Events

1. **2025-11-26**: Initial setup with potential hardcoded token
2. **2025-11-26**: Environment variables pulled out (good fix)
3. **2025-12-23**: .env files discovered in git, attempts to remove
4. **2025-12-23**: .gitignore updated to prevent future .env commits
5. **2026-02-13**: Authentication improvements made

## Current Security Posture

**Good Practices Currently in Place:**
- ✅ Secrets stored in GitHub repository secrets
- ✅ .env files properly ignored
- ✅ Environment variables used throughout code
- ✅ API token validation implemented
- ✅ CORS properly configured

**Remaining Risks:**
- ⚠️ Secrets remain in git history
- ⚠️ Previous secrets may be compromised
- ⚠️ No automated secret scanning in CI/CD

## Conclusion

While the current codebase has good security practices in place, **historical commits contain evidence of secrets being committed**. The most critical action is to **rotate all API tokens and credentials** that may have been exposed in the git history, particularly:

1. The API_TOKEN referenced in multiple commits
2. Any credentials that were in `frontend/.env.development`
3. Potentially AWS credentials if they were ever in committed .env files

The repository shows a pattern of discovering and fixing security issues over time, which is positive, but the historical exposure means all affected secrets should be treated as compromised.

## Appendix: Suspicious Commits List

| Commit SHA | Date | Message | Concern Level |
|------------|------|---------|---------------|
| `649729a2e3ec3ffb326c80827ee9b0a7e644f701` | 2025-11-26 | add api token | HIGH - mentions API token |
| `3787eafe060b6590bdc6dbf9df1c1282a87c2c66` | 2025-11-26 | env variables pulled out | MEDIUM - env variables were in code |
| `23181d9546d28704dfdfce24b43fbf5d056727a0` | 2025-12-23 | Ignore .env files | HIGH - .env files were tracked |
| `938d042ee3b9896f7b3da6db5b344ebbeb67e5a7` | 2025-12-23 | rm from history | HIGH - attempt to remove from history |
| `e218d6550d399a4cc8776d3610462ad922390de9` | 2025-12-23 | Ignore env files; stop tracking frontend/.env.development | HIGH - .env file was tracked |
| `5c043f41513449dbd60cef5474ffb70356a3da23` | 2026-02-13 | only login with correct key | MEDIUM - mentions key |

## How to Verify

To manually check what secrets were exposed, you can:

1. **Clone the full repository** (not shallow):
   ```bash
   git clone https://github.com/evnmck/cloud-app.git
   cd cloud-app
   ```

2. **Check specific commits for the .env file**:
   ```bash
   # View the .env.development file from before it was removed
   git show 938d042ee3b9896f7b3da6db5b344ebbeb67e5a7:frontend/.env.development
   
   # Or check what changed in the "add api token" commit
   git show 649729a2e3ec3ffb326c80827ee9b0a7e644f701
   ```

3. **Search for hardcoded secrets across all history**:
   ```bash
   # Search for API keys in all commits
   git log -p -S "api_key" --all
   git log -p -S "secret" --all
   git log -p -S "password" --all
   ```

4. **Use automated tools**:
   ```bash
   # Install and run truffleHog
   pip install truffleHog3
   trufflehog3 --format json .
   
   # Or use gitleaks
   docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source="/path" -v
   ```
