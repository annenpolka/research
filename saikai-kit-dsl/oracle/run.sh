#!/bin/sh
# Feeds `<SAIKAI_X>\t<value>` lines on stdin to saikai-rules' own parsers.
# `oracle/run.sh dump` prints the `on` tables and the layers' defaults.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
saikai="$here/../.saikai"
commit=$(python3 -c "import json,sys; print(json.load(open('$here/../vocab.json'))['source']['commit'])")
if [ ! -d "$saikai/.git" ]; then
  git clone -q https://gitlab.com/hidebu-reiwa/daybreak-saikai.git "$saikai"
fi
git -C "$saikai" checkout -q "$commit"
cd "$here"
exec cargo +1.97.1 run -q --manifest-path "$here/Cargo.toml" -- "$@"
