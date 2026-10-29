from typing import List, Optional
from app.schemas.review import Finding


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """
    Deduplicates findings based on (rule_id, line_number) or matching title and line_number,
    preferring deterministic AST source or higher confidence findings.
    """
    seen = {}
    deduped: List[Finding] = []

    for f in findings:
        key = (f.rule_id, f.line_number, f.category)
        if key not in seen:
            seen[key] = f
            deduped.append(f)
        else:
            existing = seen[key]
            # If current finding has higher confidence, update
            if f.confidence > existing.confidence:
                idx = deduped.index(existing)
                deduped[idx] = f
                seen[key] = f

    return deduped
