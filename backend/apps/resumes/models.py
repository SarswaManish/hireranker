"""
Resume-related models are defined in apps.candidates to avoid circular imports.
CandidateResume lives in apps/candidates/models.py.
This module re-exports it for convenience.
"""
from apps.candidates.models import CandidateResume

__all__ = ['CandidateResume']
