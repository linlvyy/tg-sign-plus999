class BusinessRetryableError(Exception):
    """Business-level error that should be retried by the task worker."""
