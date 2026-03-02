# cloud-app

Full-stack cloud platform for processing and analyzing baseball game data. Features real-time file uploads, serverless data processing pipeline, and a React frontend with JWT authentication.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (React/Vite)                         │
│  ┌──────────────────────┐              ┌──────────────────────┐          │
│  │  Login Page          │              │  Dashboard           │          │
│  │  (JWT Auth)          │◄────────────►│  (Job Status Poll)   │          │
│  └──────────────────────┘              └──────────────────────┘          │
│                │                                │                        │
│                └────────────────┬───────────────┘                        │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │ API Gateway (CORS)        │
                    │ X-API-TOKEN Header Auth   │
                    └─────────────┬─────────────┘
                                  │
┌─────────────────────────────────┼────────────────────────────────────────┐
│                         BACKEND (Lambda + AWS Services)                   │
│                                  │                                        │
│  ┌──────────────────────────────▼──────────────────┐                    │
│  │  API Lambda (handler.py)                       │                    │
│  │  ├─ POST /uploads (create job)                │                    │
│  │  ├─ GET /jobs/{jobId} (check status)          │                    │
│  │  └─ PUT /jobs/{jobId}/status (update status)  │                    │
│  └──────────────────────────────┬──────────────────┘                    │
│                                  │                                        │
│  ┌──────────────┐  ┌──────────────▼───────────┐  ┌──────────────┐       │
│  │  S3 Bucket   │  │  DynamoDB Jobs Table     │  │  Upload      │       │
│  │  (CSV/JSON)  │  │  (jobId, status, etc)    │  │  Trigger     │       │
│  └──────┬───────┘  └──────────────────────────┘  │  Lambda      │       │
│         │                                         └──────┬───────┘       │
│         │                     ┌───────────────────────────┘              │
│         │                     │                                          │
│  ┌──────▼──────────────────────▼───────────────────────┐                │
│  │  Step Function (State Machine)                     │                │
│  │  ├─ Start Glue Job                                │                │
│  │  ├─ Error Handler Lambda                          │                │
│  │  └─ Fail State (on error)                         │                │
│  └──────┬──────────────────────────────────────────────┘                │
│         │                                                               │
│  ┌──────▼──────────────────────────────────────────────┐                │
│  │  AWS Glue Job (Python 3.9)                        │                │
│  │  • Read CSV with pandas (large field support)     │                │
│  │  • Parse nested JSON recursively                  │                │
│  │  • Extract 4 data types per game:                │                │
│  │    - Game Summary (teams, scores, venue)         │                │
│  │    - Weather (temp, wind, condition)             │                │
│  │    - Play-by-Play (pitch data, events)           │                │
│  │    - Player Stats (calculated BA, OBP, SLG)      │                │
│  │  • Save processed JSON to S3                     │                │
│  │  • Update DynamoDB job status                    │                │
│  └──────────────────────────────────────────────────┘                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Data Flow: CSV Upload → S3 → Trigger Lambda → Step Function → Glue Job → 
           Processed JSON to S3 → DynamoDB status update → Frontend polling
```

## 📊 Current Status (PR1 Complete)

### ✅ Completed Features

**Data Processing Pipeline (PR1)**
- Serverless CSV upload with S3 pre-signed URLs
- AWS Glue job with pandas-based CSV processing (handles 1.4MB+ fields)
- Recursive JSON parsing for nested structures
- Defensive type checking for production data inconsistencies
- 4 data extraction functions: summary, weather, plays, player_stats
- Calculated player stats: batting average, OBP, slugging percentage
- Step Function orchestration with error handling and fail state
- DynamoDB job tracking (PENDING → PROCESSING → PROCESSED/FAILED)
- Real-time frontend polling (2-second intervals)
- Comprehensive test suite (16+ unit tests, pytest + moto)
- AWS CDK infrastructure as code

**Infrastructure**
- API Gateway with token-based auth (X-API-TOKEN header)
- 4 Lambda functions with proper IAM roles
- DynamoDB on-demand billing
- S3 with CORS configured
- VPC/networking for production readiness

**Frontend**
- React/Vite dashboard with real-time polling
- Upload form with file selection
- Job status display with download link
- Clean component architecture

### 📋 Requirements Specifications

**Data Processing**
- Input: CSV with 3 columns (gameId, date, rawData)
- CSV field size: Up to 1.4MB per row (pandas handles automatically)
- Processing time: ~15-30 seconds for 5 games
- Output: JSON array with 4+ data types per game
- Error handling: Graceful failure with status tracking

**Performance**
- Lambda concurrency: Auto-scaling
- DynamoDB: On-demand (no provisioned capacity)
- S3: Standard storage with lifecycle policies
- Glue job: Python 3.9 shell job, 15-minute timeout

**Security**
- API token authentication (dev: test token, prod: GitHub Secrets)
- CORS: Configurable by stage
- IAM least privilege for each service
- No hardcoded secrets in code
- Dependency pinning for reproducibility


## Prerequisites

- Node.js 20+
- Python 3.11+
- AWS Account with credentials configured
- Git

## Project Structure

```
cloud-app/
├── frontend/                    # React/Vite application
│   ├── src/
│   │   ├── pages/              # Login, Dashboard
│   │   ├── components/         # JobStatus, UploadForm, RequireAuth
│   │   ├── contexts/           # AuthContext
│   │   ├── api/                # API client (axios)
│   │   └── assets/
│   ├── package.json
│   ├── vite.config.js
│   └── eslint.config.js
│
├── backend/
│   ├── api/                     # API Lambda handler
│   │   ├── handler.py          # Main entry point
│   │   ├── controllers/        # Route handlers
│   │   ├── services/           # Business logic
│   │   ├── repositories/       # Data access layer
│   │   ├── models/             # Data models
│   │   ├── auth.py             # Token validation
│   │   ├── config.py           # Configuration
│   │   ├── utils.py            # Utilities
│   │   ├── requirements.txt
│   │   └── tests/              # Unit tests
│   │
│   ├── pipeline/               # S3 trigger & orchestration Lambdas
│   │   ├── upload_trigger.py   # S3 event → Step Function
│   │   ├── error_handler.py    # Catch failures from Glue
│   │   └── requirements.txt
│   │
│   └── layers/
│       └── shared/             # Lambda layer for shared code
│           └── python/
│               └── shared_services.py  # DynamoDB access
│
├── infra/                       # AWS CDK infrastructure
│   ├── app_stack.py            # Main CDK stack
│   ├── app.py                  # CDK app entry
│   ├── cdk.json
│   └── requirements.txt
│
├── data/
│   ├── glue/                    # Glue job for data processing
│   │   ├── process.py          # Extraction logic
│   │   ├── requirements.txt    # pandas, boto3
│   │   └── test_process.py     # 16+ unit tests
│   │
│   └── README.md               # Data pipeline docs
│
├── test-data/                   # Sample test data
│   ├── create_data.py          # MLB API fetcher with retry logic
│   ├── yankees_games.csv       # Test CSV
│   ├── yankees_games.json      # Raw responses
│   └── requirements.txt
│
├── README.md                    # This file
└── .github/
    └── workflows/              # GitHub Actions CI/CD
```


## Local Setup

### 1. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

Create `.env.development`:
```
VITE_API_BASE_URL=https://your-api-gateway-url/dev
```

### 2. Backend Setup (Local)

```bash
cd backend/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export STAGE=dev
export JOBS_TABLE_NAME=jobs-dev
export UPLOAD_BUCKET_NAME=upload-bucket-dev
export API_TOKEN=your-test-token
export CORS_ORIGIN=http://localhost:5173
```

For local AWS service emulation, use **AWS SAM** or **LocalStack**.

### 3. Infrastructure Setup

```bash
cd infra
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Deployment

### Prerequisites

Set up GitHub Secrets:
- `ACCOUNT_ID` - Your AWS account ID
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `API_TOKEN_DEV` - Dev API token
- `API_TOKEN_PROD` - Prod API token

### Automatic Deployment (GitHub Actions)

1. **Dev**: Deploy on pull requests targeting `main`
   ```bash
   git checkout -b feature/your-feature
   # Make changes
   git push origin feature/your-feature
   # Create PR → Auto deploys to dev
   ```

2. **Prod**: Deploy on merge to `main`
   ```bash
   git push origin main  # Triggers prod deployment
   ```

3. **Manual Trigger**: Re-deploy without code changes
   - Go to repo → Actions → Deploy CDK Stacks → Run workflow

### Local Deployment

```bash
cd infra

# Set API token
export API_TOKEN=your-secret-token

# Deploy to dev
cdk deploy MyApp-dev --require-approval never

# Deploy to prod
cdk deploy MyApp-prod --require-approval never
```

## GitHub Actions & Continuous Integration

### Automated CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment. All workflows are defined in `.github/workflows/`.

### Workflow Triggers

| Trigger | Workflow | Stage | Action |
|---------|----------|-------|--------|
| **Pull Request** | `test.yml` | - | Run all tests (Glue, API, frontend) |
| **PR to main** | `deploy.yml` | dev | Deploy to dev environment |
| **Merge to main** | `deploy.yml` | prod | Deploy to prod environment |
| **Manual (Anytime)** | `manual-test.yml` | - | Run specific or all test suites |
| **Manual (Anytime)** | `deploy.yml` | dev/prod | Redeploy without code changes |

### Test Pipeline (Runs on Every PR)

```yaml
# .github/workflows/test.yml
name: Tests

on: [pull_request, push]

jobs:
  glue-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd data/glue
          pip install -r requirements.txt
      - name: Run Glue tests
        run: cd data/glue && pytest test_process.py -v --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend/api
          pip install -r requirements.txt
      - name: Run API tests
        run: cd backend/api && pytest tests/ -v --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run ESLint
        run: cd frontend && npm run lint
```

**Test Results**: All tests must pass before merging to `main`. PR shows ✅ or ❌ status.

### Manual Test Workflow (Run Anytime)

Run tests on-demand without committing code. Useful for testing fixes, validating dependencies, or re-running after environment changes.

**How to Trigger**:

1. Go to repo → **Actions** tab
2. Click **Manual Test Run** workflow
3. Click **Run workflow** button
4. Select test suite:
   - `all` - Run Glue, API, and Frontend tests (default)
   - `glue` - Run only Glue job tests
   - `api` - Run only API Lambda tests
   - `frontend` - Run only frontend linting & build
5. Click **Run workflow**

**What Happens**:
- Selected tests run in parallel
- Coverage reports uploaded to Codecov
- Summary shows pass/fail for each suite
- Results appear in workflow run logs

**Example Scenarios**:
- ✅ After upgrading pandas: Run `glue` tests to verify
- ✅ After Glue code fix: Run `glue` tests before committing
- ✅ Validate all dependencies: Run `all` tests
- ✅ Check frontend after dependency update: Run `frontend` tests

### Deployment Pipeline (Runs on Merge or Manual Trigger)

```yaml
# .github/workflows/deploy.yml
name: Deploy CDK Stacks

on:
  push:
    branches: [main]
  workflow_dispatch:  # Manual trigger in GitHub Actions tab

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        stage: [dev, prod]
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install CDK dependencies
        run: |
          cd infra
          pip install -r requirements.txt
      
      - name: Set environment variables
        run: |
          echo "STAGE=${{ matrix.stage }}" >> $GITHUB_ENV
          echo "API_TOKEN=${{ secrets[format('API_TOKEN_{0}', matrix.stage)] }}" >> $GITHUB_ENV
      
      - name: CDK Synth
        run: cd infra && cdk synth
      
      - name: CDK Deploy
        run: cd infra && cdk deploy MyApp-${{ matrix.stage }} --require-approval never
      
      - name: Verify Deployment
        run: |
          API_URL=$(aws cloudformation describe-stacks \
            --stack-name MyApp-${{ matrix.stage }} \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
            --output text)
          curl -H "X-API-TOKEN: $API_TOKEN" $API_URL/health
```

### Testing Environment

Tests run in isolated GitHub Actions containers:
- **Glue tests**: Python 3.9 (matches Glue runtime)
- **API tests**: Python 3.11 (matches Lambda runtime)
- **Frontend tests**: Node 20 (matches production)
- **All tests**: moto for AWS service mocking (no real AWS calls)

### Test Coverage

Coverage reports are automatically uploaded to Codecov:

```bash
# View coverage locally before committing
cd data/glue
pytest test_process.py --cov --cov-report=html
open htmlcov/index.html

cd ../../backend/api
pytest tests/ --cov --cov-report=html
open htmlcov/index.html
```

### Viewing Workflow Results

1. **In GitHub**:
   - Go to repo → Actions tab
   - Click workflow run to see detailed logs
   - Each job shows status (✅ passed / ❌ failed)
   - Expand job steps to debug failures

2. **In PR**:
   - Scroll to bottom of PR
   - See "Status checks" section
   - Click "Details" to view full workflow logs

3. **Local Pre-Commit Checks** (Optional):
   ```bash
   # Run tests before committing locally
   cd data/glue && pytest test_process.py
   cd ../../backend/api && pytest tests/
   cd ../../frontend && npm run lint
   ```

### Common Workflow Issues

| Issue | Solution |
|-------|----------|
| Tests fail on PR | Check logs in Actions tab for specific error |
| Deploy fails (credentials) | Verify AWS secrets in Settings → Secrets |
| Deploy fails (CDK) | Run `cdk synth` locally to validate template |
| Token environment variable missing | Add to GitHub Secrets: `API_TOKEN_DEV`, `API_TOKEN_PROD` |
| Permissions error on S3/DynamoDB | Check IAM role attached to AWS credentials |

### Secrets Required for CI/CD

Configure these in GitHub Settings → Secrets:

```
AWS_ACCESS_KEY_ID           # IAM user access key
AWS_SECRET_ACCESS_KEY       # IAM user secret key
AWS_REGION                  # e.g., us-east-1
ACCOUNT_ID                  # Your AWS account ID
API_TOKEN_DEV               # Token for dev environment
API_TOKEN_PROD              # Token for prod environment
```

### Workflow Statistics (Monthly)

- **Tests per PR**: ~50-100 (depending on code changes)
- **Average test duration**: ~5-10 minutes
- **Deploy duration**: ~15 minutes per stage
- **Success rate target**: 100% (no merges without passing tests)

## Authentication

### Login Flow

1. User enters API token on login page
2. Frontend validates token by calling `/health` endpoint
3. Token stored in localStorage as `api_token`
4. Token automatically sent with all API requests via `X-API-TOKEN` header

### How It Works

- **Master Token**: Stored in GitHub Secrets, injected during deployment
- **Backend**: Compares request token against environment variable `API_TOKEN`
- **Requests**: Include header `X-API-TOKEN: <token>` for authentication

## API Endpoints

### Health Check
```bash
GET /health
Headers: X-API-TOKEN: <token>
Response: { "status": "ok", "stage": "dev" }
```

### Create Upload
```bash
POST /uploads
Headers: X-API-TOKEN: <token>
Body: { "fileName": "example.txt", "fileSize": 1024 }
Response: { "uploadId": "uuid", "presignedUrl": "..." }
```

### Get Job Status
```bash
GET /jobs/{jobId}
Headers: X-API-TOKEN: <token>
Response: { "jobId": "uuid", "status": "processing", ... }
```

## Environment Variables

### Frontend

`.env.development`:
```
VITE_API_BASE_URL=https://dev-api-url/dev
```

`.env.production`:
```
VITE_API_BASE_URL=https://prod-api-url/prod
```

### Backend (Lambda)

Set via CDK in `infra/app_stack.py`:
- `STAGE` - "dev" or "prod"
- `JOBS_TABLE_NAME` - DynamoDB table name
- `UPLOAD_BUCKET_NAME` - S3 bucket name
- `API_TOKEN` - Master API token
- `CORS_ORIGIN` - Allowed origin for CORS

## Security

### Best Practices

✅ **API Token Management**
- Token stored in GitHub Secrets (encrypted)
- Never commit `.env` files with real tokens
- Rotate tokens periodically
- Use different tokens for dev/prod

✅ **CORS Configuration**
- Dev: Allows `http://localhost:5173`
- Prod: Configurable via environment variable
- S3 bucket configured with restricted CORS rules

✅ **AWS Credentials**
- Only stored in GitHub Secrets
- Never committed to code
- Use IAM roles in production

✅ **Secret Scanning**
- Enabled locally via pre-commit hooks
- GitHub Actions scans for exposed secrets

### Protecting Secrets Before Push

Install pre-commit secret scanning:
```bash
pip install pre-commit detect-secrets
pre-commit install
```

## Troubleshooting

### Login Not Working

Check:
1. Is the API token correct? Compare with GitHub Secrets
2. Has the backend been redeployed after token update?
3. Is the API endpoint URL correct in `.env.development`?
4. Check browser console for API errors

### API Requests Failing with 401

1. Verify token in browser localStorage: `localStorage.getItem('api_token')`
2. Check Lambda environment variable: AWS Console → Lambda → MyApp-dev-api → Configuration
3. Ensure `X-API-TOKEN` header is being sent

### CORS Errors

1. Verify CORS is enabled in API Gateway (default configured in CDK)
2. Check S3 bucket CORS rules in AWS Console
3. Ensure frontend origin matches `CORS_ORIGIN` environment variable

## Key Technical Decisions

### CSV Processing
- **Pandas** instead of csv module: Automatic large field handling (1.4MB+)
- **Defensive type checking**: Every `.get()` call validates dict type before chaining
- **Nested JSON parsing**: Recursive conversion of string-encoded JSON to dicts

### Glue Job
- **Python 3.9 Shell job**: Lightweight, quick startup
- **Pandas dependency**: Via `--additional-python-modules` in CDK
- **Version pinning**: pandas==2.2.0 in both requirements.txt and CDK args
- **Error handling**: Exceptions raised → Step Function catch → error handler Lambda

### Step Function
- **RUN_JOB pattern**: Direct Glue invocation with task input mapping
- **Fail state on error**: Ensures execution status reflects job outcome
- **15-minute timeout**: Covers typical game data processing
- **Retry-safe naming**: UUID suffix prevents ExecutionAlreadyExists errors

### Player Stats
- **Calculated fields**: BA, OBP, SLG computed from raw stats (not from API)
- **String format**: ".500" format (e.g., "0.667") for display/analytics
- **Filtered players**: Skip entries with zero activity (0 at-bats, hits, walks)

### Authentication (Current)
- **Token-based**: Simple X-API-TOKEN header validation
- **No JWT yet**: Planned for PR2
- **Stage-aware**: Different tokens for dev/prod via GitHub Secrets

## Testing

### Glue Job Tests

```bash
cd data/glue
python -m pytest test_process.py -v
```

- 16+ unit tests with moto for AWS service mocking
- Covers: data extraction, type checking, edge cases
- All passing ✅

### API Tests

```bash
cd backend/api
python -m pytest tests/ -v --cov
```

- 24 integration tests
- Covers: authentication, CORS, error handling
- Requires: `shared_services` path in `conftest.py` ✅

### Test Data

Generate fresh test data from MLB API:
```bash
cd test-data
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python create_data.py
```

Creates: `yankees_games.csv` with 5 games of data

## Future Work (PR2-7 Roadmap)

### PR2: Authentication (BFF Lambda + JWT)
**Goal**: Replace token-based auth with JWT-based system

- Create `/auth/login` endpoint (BFF Lambda)
- Accept username/password
- Generate JWT token (10-minute expiry)
- Token refresh mechanism
- User table in DynamoDB

**Impact**: Frontend gets JWT from login, includes in Authorization header

### PR3: Frontend Auth Integration
**Goal**: Add login form and session management

- Login page component
- RequireAuth wrapper for protected routes
- JWT storage in localStorage (httpOnly cookie for production)
- Logout functionality
- Session persistence across page reloads

### PR4: E2E Test Suite
**Goal**: Test complete user workflows

- Playwright or Cypress for browser automation
- Test: login → upload → polling → success
- Test: error cases and edge conditions
- CI/CD integration

### PR5: Bedrock AI Integration
**Goal**: Generate insights from processed game data

- Lambda function for Bedrock API calls
- Prompt engineering for game summaries
- Store AI summaries in DynamoDB
- Retrieve and display in frontend

### PR6: Report Display UI
**Goal**: Beautiful report visualization

- React components for game reports
- Tabular player stats display
- Charts for trends (using Chart.js or Recharts)
- Export to PDF

### PR7: Full End-to-End Testing & Production Hardening
**Goal**: Comprehensive testing and performance optimization

- Load testing with k6 or Artillery
- Database query optimization
- Lambda layer consolidation
- Security audit
- Documentation updates

---

### Detailed PR2 Plan: JWT Authentication

#### Architecture
```
┌──────────────────┐              ┌──────────────────┐
│  Frontend        │              │  BFF Lambda      │
│  ├─ Login Form   │──POST──────► │  ├─ /auth/login  │
│  │  (user/pass)  │  /auth/login │  │  - Verify     │
│  │               │              │  │  - JWT gen     │
│  │               │◄──200────────│  │  - Store user  │
│  │   JWT token   │              │  └──────────────┘
│  │               │                      │
│  ├─ API Requests │                      │ 🆕
│  │  + JWT in     │                      ▼
│  │  header       │              ┌──────────────────┐
│  └───────────────┘              │  DynamoDB        │
│                                 │  ├─ users table  │
│                                 │  ├─ username     │
│                                 │  ├─ password (🔒)│
│                                 │  ├─ createdAt    │
│                                 │  └─ updatedAt    │
│                                 └──────────────────┘
```

#### Changes Required
1. **CDK** (`infra/app_stack.py`)
   - Add `/auth/login` POST route
   - New BFF Lambda function
   - Users DynamoDB table (username as key)

2. **Backend** (`backend/api/handler.py`)
   - New `/auth/login` endpoint
   - JWT generation (using PyJWT)
   - Password hashing (bcrypt)

3. **Frontend** (`src/pages/Login.jsx`)
   - Username/password form
   - API call to `/auth/login`
   - Store JWT in localStorage
   - Redirect to Dashboard on success

4. **Dependencies**
   - PyJWT (token generation)
   - bcrypt (password hashing)
   - cryptography (JWT signing)

#### Testing
- Unit: JWT generation, token validation
- Integration: Login flow, protected routes
- E2E: Full login to dashboard workflow

#### Timeline
- Design: 1 hour
- Implementation: 4 hours
- Testing: 2 hours
- Review: 1 hour
- **Total**: ~8 hours

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Push and create a PR (triggers dev deployment)
4. After approval, merge to `main` (triggers prod deployment)

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Environment variables configured in GitHub Secrets
- [ ] API token rotated if needed
- [ ] CORS settings appropriate for production domain
- [ ] Secrets scan shows no sensitive data in history

## Useful Commands

```bash
# Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run lint         # Run ESLint

# Backend
cdk synth           # Generate CloudFormation template
cdk diff            # Show changes before deploying
cdk destroy         # Tear down stack (use with caution)

# Git
git log -p | grep -i "token\|secret" | grep -v "REMOVED_SECRET"  # Scan for secrets
git filter-repo --replace-text replacements.txt --force           # Remove secrets from history
```

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)

## License

MIT
