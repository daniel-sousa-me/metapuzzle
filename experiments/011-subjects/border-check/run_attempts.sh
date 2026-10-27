#!/bin/bash
# Try standard border with quarter rotation and N extra flat pieces; stop at the first valid run.
cd /home/user/metapuzzle/experiments/011-subjects
for N in 0 20 40 80; do
  echo "=== N=$N $(date +%T)"
  metapuzzle prototype --scenes pipeline/v3/scenes.txt --classes pipeline/classes-v9.json \
    --out border-check/run-standard-x$N --border standard --rotation quarter --cell 21 --extra-flat $N \
    > border-check/stdout-x$N.txt 2> border-check/stderr-x$N.txt
  rc=$?
  echo "exit=$rc $(date +%T)"
  if [ $rc -eq 0 ]; then echo "FIRST_VALID=$N"; break; fi
done
echo DONE
