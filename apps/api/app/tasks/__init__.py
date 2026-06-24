"""Background task handlers executed by the RQ worker (``python -m app.worker``).

Each task opens its own database session and commits its own unit of work, since
it runs outside the request lifecycle.
"""
