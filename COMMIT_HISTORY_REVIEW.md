# Complete Commit History - Security Review

This document lists all 34 commits in the repository with direct links for easy review.

## How to Use This Document

1. Click on any commit link to view it on GitHub
2. Review the diff to see what changed
3. Look for hardcoded secrets, API keys, or credentials
4. Pay special attention to commits marked with ⚠️

## Commits Requiring Immediate Review

### 🚨 HIGH PRIORITY

| # | Date | Commit | Message | Action Required |
|---|------|--------|---------|-----------------|
| 32 | 2025-11-26 | [649729a2](https://github.com/evnmck/cloud-app/commit/649729a2e3ec3ffb326c80827ee9b0a7e644f701) | add api token | ⚠️ Check if token was hardcoded |
| 31 | 2025-11-26 | [3787eafe](https://github.com/evnmck/cloud-app/commit/3787eafe060b6590bdc6dbf9df1c1282a87c2c66) | env variables pulled out | ⚠️ Check what values were in code before |
| 24 | 2025-12-23 | [e218d655](https://github.com/evnmck/cloud-app/commit/e218d6550d399a4cc8776d3610462ad922390de9) | Ignore env files; stop tracking frontend/.env.development | ⚠️ View the deleted .env.development file |
| 25 | 2025-12-23 | [938d042e](https://github.com/evnmck/cloud-app/commit/938d042ee3b9896f7b3da6db5b344ebbeb67e5a7) | rm from history | ⚠️ View what was being removed |
| 26 | 2025-12-23 | [23181d95](https://github.com/evnmck/cloud-app/commit/23181d9546d28704dfdfce24b43fbf5d056727a0) | Ignore .env files | ⚠️ Related to .env tracking |

### ⚠️ MEDIUM PRIORITY

| # | Date | Commit | Message | Notes |
|---|------|--------|---------|-------|
| 7 | 2026-02-13 | [5c043f41](https://github.com/evnmck/cloud-app/commit/5c043f41513449dbd60cef5474ffb70356a3da23) | only login with correct key | Review authentication implementation |

## Complete Commit History

| # | Date | Commit | Message |
|---|------|--------|---------|
| 1 | 2026-02-13 | [3cdc0026](https://github.com/evnmck/cloud-app/commit/3cdc002634f40d13f5654695dd8a543c292e6b62) | Merge pull request #7 from evnmck/feature/manual-deployment2 |
| 2 | 2026-02-13 | [6d6d3ea7](https://github.com/evnmck/cloud-app/commit/6d6d3ea736dccc1f58e107b666798fb5f1474da8) | remove comment |
| 3 | 2026-02-13 | [ffcf52bd](https://github.com/evnmck/cloud-app/commit/ffcf52bd516effce86a1eebe59be0b519499e333) | deploy via github actions |
| 4 | 2026-02-13 | [698a5db6](https://github.com/evnmck/cloud-app/commit/698a5db6263f8b1e5a8c4746b55841eb86782324) | Merge pull request #6 from evnmck/feature/manual-deployment |
| 5 | 2026-02-13 | [f178c279](https://github.com/evnmck/cloud-app/commit/f178c2793cc70333305c8b98e6471c9ed5d10385) | deploy via github actions |
| 6 | 2026-02-13 | [4be5ea90](https://github.com/evnmck/cloud-app/commit/4be5ea9036734cdd2780a947e03be1d6e93ec00c) | Merge pull request #5 from evnmck/feature/update-login |
| 7 | 2026-02-13 | [5c043f41](https://github.com/evnmck/cloud-app/commit/5c043f41513449dbd60cef5474ffb70356a3da23) | only login with correct key ⚠️ |
| 8 | 2025-12-24 | [384d9c36](https://github.com/evnmck/cloud-app/commit/384d9c36f891e7cc8b574483a898c2c4b532de83) | Merge pull request #4 from evnmck/fix/s3-file-naming |
| 9 | 2025-12-24 | [1e0611b8](https://github.com/evnmck/cloud-app/commit/1e0611b8bc7dd5be24e7fdc1a11ffe8f7aa74265) | update to not create new folder for each upload |
| 10 | 2025-12-23 | [514656f7](https://github.com/evnmck/cloud-app/commit/514656f7ab717e4ed80be0f4768f26e4522bba49) | Merge pull request #2 from evnmck/feature/frontend |
| 11 | 2025-12-23 | [8157681b](https://github.com/evnmck/cloud-app/commit/8157681ba9a02a6edbb4817327b4df16e5362574) | Merge pull request #3 from evnmck/copilot/sub-pr-2 |
| 12 | 2025-12-23 | [71b00c24](https://github.com/evnmck/cloud-app/commit/71b00c24330d3df1bb2a21cce152297ea6f0d406) | Handle wildcard CORS origin explicitly for API Gateway |
| 13 | 2025-12-23 | [bb56faa8](https://github.com/evnmck/cloud-app/commit/bb56faa8627c5933886719d07522d7598f8f90c6) | Make CORS origin configurable via environment variable |
| 14 | 2025-12-23 | [62493c27](https://github.com/evnmck/cloud-app/commit/62493c27f24e8c01a8eef7bda43dc11e947cd08d) | Initial plan |
| 15 | 2025-12-23 | [b623b130](https://github.com/evnmck/cloud-app/commit/b623b1302bead6e625ca9581e7a07af82927c7b9) | Update backend/pipeline/upload_handler.py |
| 16 | 2025-12-23 | [97b44c35](https://github.com/evnmck/cloud-app/commit/97b44c350e0b952dae1e26ed2c91924bcdb1642a) | Update frontend/src/pages/Login.jsx |
| 17 | 2025-12-23 | [17f3757f](https://github.com/evnmck/cloud-app/commit/17f3757fd79d2d8d59ec9e999f3a851a8f83ebc7) | Update backend/api/handler.py |
| 18 | 2025-12-23 | [1485848c](https://github.com/evnmck/cloud-app/commit/1485848c00fcf7a827d716697687809f5bcce568) | fix login |
| 19 | 2025-12-23 | [4d1e7cd2](https://github.com/evnmck/cloud-app/commit/4d1e7cd27114fb737ade4cf105de1617dcedd393) | login page |
| 20 | 2025-12-23 | [3efc6ab6](https://github.com/evnmck/cloud-app/commit/3efc6ab6d84fbdab40a9962cd1b264f1fbd9ae7c) | remove files |
| 21 | 2025-12-23 | [107c0cd6](https://github.com/evnmck/cloud-app/commit/107c0cd65689399821b61de36ff7e6ec56662105) | Remove legacy App.css, App.jsx and index.css |
| 22 | 2025-12-23 | [cd0863e1](https://github.com/evnmck/cloud-app/commit/cd0863e1cd9c6a9649def7a4cea8ab697e72a9ca) | update to only deploy when needed |
| 23 | 2025-12-23 | [e218d655](https://github.com/evnmck/cloud-app/commit/e218d6550d399a4cc8776d3610462ad922390de9) | Ignore env files; stop tracking frontend/.env.development ⚠️ |
| 24 | 2025-12-23 | [938d042e](https://github.com/evnmck/cloud-app/commit/938d042ee3b9896f7b3da6db5b344ebbeb67e5a7) | rm from history ⚠️ |
| 25 | 2025-12-23 | [23181d95](https://github.com/evnmck/cloud-app/commit/23181d9546d28704dfdfce24b43fbf5d056727a0) | Ignore .env files ⚠️ |
| 26 | 2025-12-23 | [b3fe465d](https://github.com/evnmck/cloud-app/commit/b3fe465d0e80036c0828a0531f4984ad19eef28e) | consolidate git ignore |
| 27 | 2025-12-23 | [5e6a5adf](https://github.com/evnmck/cloud-app/commit/5e6a5adff96dce07bf43aef8b2446d976e2e3d45) | add to gitignore |
| 28 | 2025-12-23 | [fbcb724d](https://github.com/evnmck/cloud-app/commit/fbcb724de2d61d640bf001af3e3fcb4c7db46c9e) | stops from creating new folder per upload |
| 29 | 2025-12-03 | [e91dd607](https://github.com/evnmck/cloud-app/commit/e91dd6074f4023c73970c2df65d09ffcac1312a1) | add temp front end |
| 30 | 2025-11-26 | [68d61992](https://github.com/evnmck/cloud-app/commit/68d61992d7796964ef83d0841549ce448b3c48a9) | Merge pull request #1 from evnmck/setup |
| 31 | 2025-11-26 | [649729a2](https://github.com/evnmck/cloud-app/commit/649729a2e3ec3ffb326c80827ee9b0a7e644f701) | add api token 🚨 |
| 32 | 2025-11-26 | [3787eafe](https://github.com/evnmck/cloud-app/commit/3787eafe060b6590bdc6dbf9df1c1282a87c2c66) | env variables pulled out 🚨 |
| 33 | 2025-11-26 | [2aa8a06b](https://github.com/evnmck/cloud-app/commit/2aa8a06b0ed0b54d36c59ed1945e9c5ffc6f245b) | infra setup and github actions setup |
| 34 | 2025-11-26 | [3d09db9f](https://github.com/evnmck/cloud-app/commit/3d09db9f9871b37c5ac980e71c2295eae1aaa969) | Initial commit |

## Quick Commands to Review Specific Files

To view what was in the .env.development file before it was removed:

```bash
# Clone the full repository (not shallow)
git clone https://github.com/evnmck/cloud-app.git
cd cloud-app

# View the .env.development file from the commit where it was added back
git show 938d042ee3b9896f7b3da6db5b344ebbeb67e5a7:frontend/.env.development

# Or see what was removed in the commit that deleted it
git show e218d6550d399a4cc8776d3610462ad922390de9
```

To see what changed when "add api token" was committed:

```bash
# View the full diff
git show 649729a2e3ec3ffb326c80827ee9b0a7e644f701

# Or view it on GitHub
open https://github.com/evnmck/cloud-app/commit/649729a2e3ec3ffb326c80827ee9b0a7e644f701
```

To search for all occurrences of a specific secret pattern:

```bash
# Search for "api" in all commits
git log -p -S "api" --all

# Search for potential API keys
git log -p -S "api_key" --all
git log -p -S "secret" --all
```

## Next Steps

1. **Review the 6 commits marked with ⚠️ and 🚨** - These are most likely to contain secrets
2. **Rotate all credentials** that might have been exposed
3. **Follow the recommendations** in SECURITY_AUDIT_REPORT.md
4. **Enable GitHub Secret Scanning** to prevent future issues

## Tools to Help

- **TruffleHog**: `pip install truffleHog3 && trufflehog3 .`
- **gitleaks**: `docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source="/path" -v`
- **git-secrets**: `brew install git-secrets` (prevents committing secrets)
- **GitHub Secret Scanning**: Enable in repository settings (Advanced Security)

---
**Note**: This list was generated on 2026-02-13 as part of a security audit. All commit links point to the GitHub web interface for easy review.
