"""
My scoring rule for run_eval.py.

An answer counts as correct when it contains the `expects` phrase from
questions.py and names a source file. Both halves matter: criterion 2 says
every answer names a source, so an unsourced right answer is not a pass.
"""

import re

import gate


def normalise(text: str) -> str:
    """Lowercase, and drop spacing and punctuation that shouldn't change a verdict."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def judge(question: str, expects: str, answer: str, results) -> bool:
    if not answer or answer.strip() == gate.REFUSAL.strip():
        return False

    if normalise(expects) not in normalise(answer):
        return False

    return bool(re.search(r"[\w-]+\.(txt|md)", answer))
