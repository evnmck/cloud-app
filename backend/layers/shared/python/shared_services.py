import re
from shared_repositories import update_job_repository

VALID_STATUSES = ['PENDING_UPLOAD', 'UPLOADED', 'PROCESSING', 'PROCESSED', 'COMPLETED', 'FAILED']

# Define allowed extra fields and their expected types
ALLOWED_FIELDS = {
    'processedDataLocation': str,
    'error': str,
}

# Validation rules for each field
FIELD_VALIDATORS = {
    'processedDataLocation': {
        'max_length': 500,
        'pattern': r'^s3://[\w\-\.]+/[\w\-\./_]+$',  # s3://bucket/key format
        'description': 'Must be valid S3 URL'
    },
    'error': {
        'max_length': 1000,
        'pattern': r'^[\w\s\-\.,:;()]+$',  # Alphanumeric + basic punctuation
        'description': 'Can only contain letters, numbers, spaces, and basic punctuation'
    }
}

def validate_string_field(field_name: str, value: str) -> None:
    """Validate string field format and content"""
    if field_name not in FIELD_VALIDATORS:
        raise ValueError(f"No validation rules for field '{field_name}'")
    
    rules = FIELD_VALIDATORS[field_name]
    
    # Check length
    if len(value) > rules['max_length']:
        raise ValueError(f"Field '{field_name}' exceeds max length {rules['max_length']}")
    
    # Check pattern
    if not re.match(rules['pattern'], value):
        raise ValueError(f"Field '{field_name}': {rules['description']}")

def update_job(job_id: str, status: str, **extra_fields):
    """Update job status with validation"""
    
    # Validate inputs
    if not job_id or not isinstance(job_id, str):
        raise ValueError("job_id must be a non-empty string")
    
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}")
    
    # Validate extra fields
    for key, value in extra_fields.items():
        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Unknown field: '{key}'. Allowed: {', '.join(ALLOWED_FIELDS.keys())}")
        
        if not isinstance(value, str):
            raise ValueError(f"Field '{key}' must be string, got {type(value).__name__}")
        
        if not value:  # Empty string check
            raise ValueError(f"Field '{key}' cannot be empty")
        
        # Validate field-specific rules
        validate_string_field(key, value)
    
    # Call repository
    update_job_repository(job_id, status, **extra_fields)