# Conventions

## Git
- **Branches:** `type/short-description`, lowercase with hyphens. Example: `feat/ml-training`.
- **Commits and PR titles:** Conventional Commits, `type(scope): summary`. Imperative, lowercase, under ~72 characters. Example: `feat(ml): add baseline training notebook`.
- **Types:** feat, fix, docs, chore, refactor, test, ci, exp.
- **Scopes:** ml, backend, frontend, infra, docs.
- Every change goes through a pull request and is squash-merged. A new branch starts from an updated `main`.

## Code
- **Python:** PEP 8. `snake_case` for files, functions and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants. Scripts start with a verb (`convert_rdd_to_yolo.py`). Formatted and linted with Ruff.
- **Frontend:** `PascalCase` for React components (`ReportCard.tsx`), `camelCase` for functions and variables.
- **Comments** explain why, not what.

## ML
- **Notebooks:** `NN_verb_description.ipynb`, numbered in run order (`01_train_baseline.ipynb`).
- **Datasets:** short name plus version. `rdd5-v1` = RDD2022, five countries, split version 1.
- **Experiments:** `eNNN-model-dataset-change`, sequential. `e001-yolo26s-rdd5-baseline`.
- **Weights:** `dupka-model-experiment.pt`. `dupka-yolo26s-e001.pt`.
- Every experiment is logged in `ml/EXPERIMENTS.md`.

## Docs
- **Decision records:** `docs/decisions/NNNN-kebab-title.md`.
