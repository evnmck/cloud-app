# cloud-app

A full-stack cloud application with React frontend, Python Lambda backend, and AWS infrastructure managed via CDK.

## Architecture

- **Frontend**: React + Vite (TypeScript/JavaScript)
- **Backend**: Python Lambda functions with API Gateway
- **Infrastructure**: AWS CDK (Python)
- **Database**: DynamoDB (for job storage)
- **Storage**: S3 (for file uploads)
- **CI/CD**: GitHub Actions (automated deployments)

## Prerequisites

- Node.js 20+
- Python 3.11+
- AWS Account with credentials configured
- Git

## Project Structure

```
cloud-app/
├── frontend/              # React/Vite application
│   ├── src/
│   │   ├── pages/        # Login, Dashboard
│   │   ├── components/   # JobStatus, UploadForm, etc.
│   │   ├── contexts/     # AuthContext
│   │   └── api/          # API client
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── api/              # API Lambda handler
│   └── pipeline/         # S3 event handler
├── infra/                # AWS CDK stacks
│   ├── app_stack.py      # Main infrastructure definition
│   ├── requirements.txt
│   └── cdk.json
├── data/                 # Data pipeline scripts
└── test-data/            # Sample test data
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
