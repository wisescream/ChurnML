# Release & Push Checklist

Use this checklist before pushing changes to the shared repository:

1. **Verify quality gates**
   - `python -m pytest`
   - Optional: `dvc repro` and review updated metrics in `metrics.json`.
2. **Validate documentation**
   - Confirm `README.md` reflects the latest workflows, endpoints, and deployment details.
   - Update notebook narratives and regenerate static figures if needed.
3. **Review artifacts**
   - Ensure generated files (`data/processed/`, `models/`, `metrics.json`, `mlruns/`) are not committed directly; use DVC for large artifacts.
   - Run `dvc status` to confirm tracked outputs are in sync.
4. **Security & credentials**
   - Validate that secrets remain in environment variables or secret managers—not in Git.
   - Check CI secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc.) are still valid.
5. **Git hygiene**
   - `git status` should show only intentional source changes.
   - Craft meaningful commit messages summarising scope and impact.
   - Push main branch updates with `git push origin main` (or use feature branches and pull requests).

Automating these checks via GitHub Actions or pre-push hooks is recommended as the project matures.
