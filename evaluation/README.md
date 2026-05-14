# Evaluation Workspace

This directory contains the starter assets for SPARA evaluation-readiness work.

Current scope:
- seed evaluation cases
- seed ground-truth building data
- seed advisor reference answers
- advisor review CSV template
- question-bank import script
- direct `AgentRouter` evaluation runner
- metric summarizer
- advisor review sheet exporter

Recommended first workflow:

```bash
python evaluation/scripts/import_question_bank.py <path-to-question-bank>
python evaluation/scripts/run_eval_cases.py --evaluation-mode
python evaluation/scripts/analyze_eval_results.py
python evaluation/scripts/export_advisor_review_sheet.py
```

Notes:
- The runner currently uses the direct `AgentRouter` path for faster iteration.
- The seed datasets are placeholders and should be replaced with verified BRF data before formal evaluation.
- Results are written to `evaluation/results/`.
