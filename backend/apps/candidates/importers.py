import logging
import io
import re
from typing import Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Maximum import file size
MAX_IMPORT_FILE_SIZE = getattr(settings, 'MAX_IMPORT_FILE_SIZE', 10 * 1024 * 1024)

ALLOWED_MIME_TYPES = {
    'text/csv',
    'text/plain',
    'application/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

# Column name aliases for auto-detection
COLUMN_ALIASES = {
    'name': [
        'name', 'full_name', 'fullname', 'candidate_name', 'applicant_name',
        'candidate', 'applicant', 'full name', 'candidate name',
    ],
    'email': [
        'email', 'email_address', 'emailaddress', 'e-mail', 'email address',
        'mail', 'contact_email',
    ],
    'phone': [
        'phone', 'phone_number', 'phonenumber', 'mobile', 'contact', 'telephone',
        'phone number', 'mobile number', 'contact number',
    ],
    'location': [
        'location', 'city', 'address', 'current_location', 'current location',
        'place', 'residence', 'hometown',
    ],
    'college': [
        'college', 'university', 'school', 'institution', 'college_name',
        'university name', 'college name', 'alma_mater',
    ],
    'degree': [
        'degree', 'education', 'qualification', 'degree_type', 'degree type',
        'highest_qualification', 'course',
    ],
    'graduation_year': [
        'graduation_year', 'grad_year', 'passing_year', 'year_of_passing',
        'graduation year', 'passing year', 'batch', 'batch_year',
    ],
    'cgpa': [
        'cgpa', 'gpa', 'grade', 'percentage', 'marks', 'score',
        'aggregate', 'cgpa/percentage',
    ],
    'skills': [
        'skills', 'technical_skills', 'technologies', 'tech_stack',
        'skills set', 'core_skills', 'key skills',
    ],
    'github_url': [
        'github', 'github_url', 'github_link', 'github url', 'github profile',
    ],
    'linkedin_url': [
        'linkedin', 'linkedin_url', 'linkedin_link', 'linkedin url', 'linkedin profile',
    ],
    'portfolio_url': [
        'portfolio', 'portfolio_url', 'portfolio_link', 'website', 'personal_website',
        'portfolio url', 'personal website',
    ],
    'resume_url': [
        'resume', 'resume_url', 'resume_link', 'cv', 'cv_link', 'resume url',
        'resume link', 'cv url', 'drive_link', 'google_drive',
    ],
    'notes': [
        'notes', 'comments', 'remarks', 'feedback', 'note',
    ],
}


def validate_file(file) -> tuple[bool, str]:
    """
    Validate an uploaded import file.

    Args:
        file: Django uploaded file object

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Check file size
    if file.size > MAX_IMPORT_FILE_SIZE:
        size_mb = MAX_IMPORT_FILE_SIZE / (1024 * 1024)
        return False, f"File size exceeds maximum allowed size of {size_mb:.0f}MB"

    # Check file extension
    import os
    _, ext = os.path.splitext(file.name.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    # Try to read to validate it's a valid file
    try:
        if ext in ['.xlsx', '.xls']:
            import openpyxl
            file.seek(0)
            openpyxl.load_workbook(file, read_only=True)
            file.seek(0)
        elif ext == '.csv':
            file.seek(0)
            content = file.read(1024)
            file.seek(0)
            # Basic validation that it looks like text
            content.decode('utf-8', errors='replace')
    except Exception as e:
        return False, f"File appears to be corrupt or invalid: {str(e)}"

    return True, ''


def detect_columns(df) -> dict:
    """
    Auto-detect column mappings from a DataFrame.

    Args:
        df: pandas DataFrame

    Returns:
        Dict mapping our field names to DataFrame column names
    """
    df_columns_lower = {col.lower().strip(): col for col in df.columns}
    mapping = {}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in df_columns_lower:
                mapping[field] = df_columns_lower[alias.lower()]
                break

    return mapping


def normalize_candidate_data(row: dict, column_mapping: dict) -> dict:
    """
    Normalize a single row of data using the column mapping.

    Args:
        row: Dict representing one row of data
        column_mapping: Dict mapping field names to column names

    Returns:
        Normalized dict suitable for Candidate creation
    """
    data = {}

    def get_val(field):
        col = column_mapping.get(field)
        if col and col in row:
            val = row[col]
            if val is None:
                return ''
            if hasattr(val, '__float__') and str(val) == 'nan':
                return ''
            return str(val).strip()
        return ''

    data['name'] = get_val('name')
    data['email'] = get_val('email').lower() if get_val('email') else ''
    data['phone'] = get_val('phone')
    data['location'] = get_val('location')
    data['college'] = get_val('college')
    data['degree'] = get_val('degree')
    data['github_url'] = _normalize_url(get_val('github_url'))
    data['linkedin_url'] = _normalize_url(get_val('linkedin_url'))
    data['portfolio_url'] = _normalize_url(get_val('portfolio_url'))
    data['resume_url'] = _normalize_url(get_val('resume_url'))
    data['notes'] = get_val('notes')

    # Skills - try to parse as list
    skills_raw = get_val('skills')
    data['skills'] = _parse_skills(skills_raw)

    # Graduation year
    grad_year_raw = get_val('graduation_year')
    data['graduation_year'] = _parse_year(grad_year_raw)

    # CGPA
    cgpa_raw = get_val('cgpa')
    data['cgpa'] = _parse_decimal(cgpa_raw)

    return data


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if not url:
        return ''
    url = url.strip()
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url[:1000]


def _parse_skills(skills_raw: str) -> list:
    """Parse skills string into a list."""
    if not skills_raw:
        return []
    # Split by common delimiters
    skills = re.split(r'[,;|/\n\r]+', skills_raw)
    return [s.strip() for s in skills if s.strip()][:50]  # Cap at 50 skills


def _parse_year(year_raw: str) -> Optional[int]:
    """Parse a year string to integer."""
    if not year_raw:
        return None
    # Extract 4-digit year
    match = re.search(r'\b(19|20)\d{2}\b', year_raw)
    if match:
        year = int(match.group())
        if 1970 <= year <= 2035:
            return year
    # Try direct int conversion
    try:
        year = int(float(year_raw))
        if 1970 <= year <= 2035:
            return year
    except (ValueError, OverflowError):
        pass
    return None


def _parse_decimal(val_raw: str) -> Optional[float]:
    """Parse a decimal value (CGPA/percentage)."""
    if not val_raw:
        return None
    # Extract numeric value
    match = re.search(r'\d+\.?\d*', val_raw)
    if match:
        try:
            val = float(match.group())
            # Normalize percentage to 0-10 scale if it's > 10
            if val > 10:
                val = val / 10
            if 0 <= val <= 10:
                return round(val, 2)
        except ValueError:
            pass
    return None


def import_candidates_from_file(batch, file, column_mapping: dict) -> tuple[int, int, list]:
    """
    Import candidates from a CSV or XLSX file.

    Args:
        batch: CandidateImportBatch instance
        file: Django file object or file path
        column_mapping: Dict mapping field names to column names

    Returns:
        Tuple of (processed_count, failed_count, errors)
    """
    import pandas as pd
    import numpy as np
    from apps.candidates.models import Candidate

    errors = []
    processed = 0
    failed = 0

    try:
        # Read file
        file_name = batch.file_name.lower()
        if hasattr(file, 'seek'):
            file.seek(0)

        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            df = pd.read_excel(file, dtype=str)
        else:
            # Try multiple encodings for CSV
            if hasattr(file, 'read'):
                content = file.read()
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(content), dtype=str, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file")
            else:
                df = pd.read_csv(file, dtype=str)

        # Replace NaN with None
        df = df.where(pd.notnull(df), None)

        # Auto-detect columns if no mapping provided
        if not column_mapping:
            column_mapping = detect_columns(df)

        batch.total_rows = len(df)
        batch.column_mapping = column_mapping
        batch.save()

        candidates_to_create = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 for header and 0-index
            try:
                data = normalize_candidate_data(row.to_dict(), column_mapping)

                if not data.get('name'):
                    errors.append({'row': row_num, 'error': 'Name is required'})
                    failed += 1
                    continue

                candidate = Candidate(
                    project=batch.project,
                    batch=batch,
                    name=data['name'],
                    email=data['email'],
                    phone=data['phone'],
                    location=data['location'],
                    college=data['college'],
                    degree=data['degree'],
                    graduation_year=data['graduation_year'],
                    cgpa=data['cgpa'],
                    skills=data['skills'],
                    github_url=data['github_url'],
                    linkedin_url=data['linkedin_url'],
                    portfolio_url=data['portfolio_url'],
                    resume_url=data['resume_url'],
                    notes=data['notes'],
                    raw_data={str(k): str(v) if v is not None else '' for k, v in row.to_dict().items()},
                    status=Candidate.Status.PENDING,
                )
                candidates_to_create.append(candidate)
                processed += 1

            except Exception as e:
                logger.warning("Row %d import error: %s", row_num, e)
                errors.append({'row': row_num, 'error': str(e)})
                failed += 1

        # Bulk create candidates
        if candidates_to_create:
            Candidate.objects.bulk_create(candidates_to_create, batch_size=500)

    except Exception as e:
        logger.error("Import batch %s failed: %s", batch.id, e)
        errors.append({'row': 0, 'error': f'File processing failed: {str(e)}'})
        failed = batch.total_rows - processed

    return processed, failed, errors


def detect_duplicates(project, candidates=None) -> int:
    """
    Detect and mark duplicate candidates within a project.

    Args:
        project: HiringProject instance
        candidates: Optional queryset of candidates to check (defaults to all in project)

    Returns:
        Number of duplicates found
    """
    from apps.candidates.models import Candidate

    if candidates is None:
        candidates = Candidate.objects.filter(project=project, is_duplicate=False)

    duplicate_count = 0

    # Build email index for deduplication
    email_to_first = {}
    for candidate in candidates.order_by('created_at'):
        if candidate.email:
            email_lower = candidate.email.lower()
            if email_lower in email_to_first:
                original = email_to_first[email_lower]
                candidate.is_duplicate = True
                candidate.duplicate_of = original
                candidate.save(update_fields=['is_duplicate', 'duplicate_of'])
                duplicate_count += 1
            else:
                email_to_first[email_lower] = candidate

    logger.info("Found %d duplicates in project %s", duplicate_count, project.id)
    return duplicate_count
