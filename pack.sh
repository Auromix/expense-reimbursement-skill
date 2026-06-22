#!/usr/bin/env bash
# Build the installable .skill package (a zip containing the expense-reimbursement/ folder).
set -euo pipefail
cd "$(dirname "$0")"
OUT="dist/expense-reimbursement.skill"
mkdir -p dist
rm -f "$OUT"
zip -r -q "$OUT" expense-reimbursement \
  -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store"
echo "Built $OUT"
