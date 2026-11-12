#!/usr/bin/env bash
# Authorized HPC only. Offline checks, no API or training.
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${PYTHON:-python}"
evidence="${1:?Supply a new absolute HPC evidence directory}"
test ! -e "$evidence"
mkdir -p "$evidence"
git rev-parse HEAD > "$evidence/commit.txt"
"$python_bin" -m compileall -q agt tests > "$evidence/compileall.log" 2>&1
"$python_bin" -m unittest discover -s tests -v > "$evidence/unit-tests.log" 2>&1
"$python_bin" -m agt.cli demo --backend fixture --scenario investment --output "$evidence/fixture" > "$evidence/fixture.log" 2>&1
"$python_bin" -m agt.train "$evidence/fixture/training.jsonl" > "$evidence/pair-validation.log" 2>&1
tail -n 4 "$evidence/unit-tests.log"
cat "$evidence/pair-validation.log"
printf 'Offline HPC checks passed: %s\n' "$evidence"
