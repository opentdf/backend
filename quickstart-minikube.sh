#!/usr/bin/env bash
set -euo pipefail

tilt ci

printf "\nAll Done! Fire up 'octant' or similar to have a look at the cluster\n"
