#!/bin/sh
# Optional maintenance task: committed derivatives need no encoder at deployment.
# Requires cwebp (libwebp); run from any working directory.
set -eu
images="$(CDPATH= cd -- "$(dirname -- "$0")/../static/website/images" && pwd)"
for name in camp olympus trident; do
  for width in 256 384 512 768; do
    cwebp -quiet -q 85 -m 6 -metadata none -resize "$width" 0 \
      "$images/lore-$name.webp" -o "$images/lore-$name-$width.webp"
  done
done
