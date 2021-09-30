#!/usr/bin/env bash
python -O -m pytest \
  --benchmark-enable \
  --benchmark-only \
  --benchmark-save-data \
  --benchmark-sort=name \
  --benchmark-name=short \
  --benchmark-columns=min,mean,median,iqr,rounds,iterations \
  --benchmark-autosave \
  "$@"
