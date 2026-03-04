"""Input validation for security and stability."""


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_query(query: str, max_length: int = 1000) -> str:
    """
    Validate and sanitize user query.

    Args:
        query: User query string
        max_length: Maximum allowed query length (default 1000)

    Returns:
        Sanitized query string

    Raises:
        ValidationError: If query is invalid
    """
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")

    query = query.strip()

    if len(query) > max_length:
        # Truncate to max length
        query = query[:max_length]

    return query


def validate_subject_id(subject_id: str, max_length: int = 100) -> str:
    """
    Validate subject ID (alphanumeric + underscore/hyphen only).

    This prevents injection attacks and ensures subject IDs are safe
    to use in authorization checks.

    Args:
        subject_id: User/subject identifier
        max_length: Maximum allowed length (default 100)

    Returns:
        Sanitized subject ID

    Raises:
        ValidationError: If subject ID is invalid
    """
    if not subject_id or not subject_id.strip():
        raise ValidationError("Subject ID cannot be empty")

    subject_id = subject_id.strip()

    if len(subject_id) > max_length:
        raise ValidationError(f"Subject ID too long (max {max_length} characters)")

    # Only allow alphanumeric, underscore, and hyphen
    if not all(c.isalnum() or c in ["_", "-"] for c in subject_id):
        raise ValidationError(
            "Subject ID contains invalid characters (only alphanumeric, underscore, and hyphen allowed)"
        )

    return subject_id
