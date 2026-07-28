# Project Mining Workspace

Start with the [mining plan](project-insight-mining-plan.md). Generate a local,
metadata-only census without copying project contents:

```bash
python scripts/inventory_projects.py --root /projects --output research/corpus-manifest.yaml
```

Then:

1. Review every candidate's privacy classification and repository instructions.
2. Establish Socratic provenance; a file named `SPEC.md` is not sufficient.
3. Select a stratified first wave and copy `project-review.template.yaml` for each.
4. Calibrate two reviewers on the same two projects before parallel extraction.
5. Synthesize cross-project lessons only after factual extraction is complete.

Generated `corpus-manifest.yaml` is a local research artifact. Review it before
committing because repository paths or project names may be unsuitable for export.
