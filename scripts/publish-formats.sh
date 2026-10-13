#!/usr/bin/env bash
# Publish the formats catalogue to the PUBLIC registry and update its latest-pointer.
# The catalogue is a versioned artifact (agents/formats.json declares its own CalVer
# version); published versions are immutable — this script refuses to overwrite an
# existing version. The engine loads a pinned version at startup (B2, #1001), so
# activating a new catalogue is: publish, bump the pin if concrete, restart the Function App.
#
# Usage:
#   ./scripts/publish-formats.sh <storage-account>
# Example:
#   ./scripts/publish-formats.sh consultpubcaeast
set -euo pipefail

CONTAINER="formats"
AGENTS_DIR="agents"
INDEX="$AGENTS_DIR/formats.json"

if [[ $# -ne 1 ]]; then
	grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -10
	exit 1
fi

ACCOUNT="$1"

[[ -f "$INDEX" ]] || { echo "error: $INDEX not found (run from the repo root)" >&2; exit 1; }

VERSION=$(python3 -c "import json;print(json.load(open('$INDEX'))['version'])")

if ! [[ "$VERSION" =~ ^v[0-9]{4}\.(0[1-9]|1[0-2])\.[1-9][0-9]*$ ]]; then
	echo "error: formats version '$VERSION' is not vYYYY.MM.N" >&2
	exit 1
fi

AUTH=(--account-name "$ACCOUNT" --auth-mode "${AZ_STORAGE_AUTH_MODE:-login}")

if az storage blob exists "${AUTH[@]}" --container-name "$CONTAINER" \
	--name "$VERSION/formats.json" --query exists -o tsv | grep -q true; then
	echo "error: formats@$VERSION is already published; versions are immutable — bump the version" >&2
	exit 1
fi

# Format files first, the index last (the loader resolves the index first, so a
# partial upload is invisible).
python3 -c "
import json
for e in json.load(open('$INDEX'))['formats'].values():
    print(e['file'])
" | sort -u | while read -r FILE; do
	[[ -f "$AGENTS_DIR/$FILE" ]] || { echo "error: format file $AGENTS_DIR/$FILE not found" >&2; exit 1; }
	echo "Uploading $VERSION/$FILE"
	az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
		--file "$AGENTS_DIR/$FILE" --name "$VERSION/$FILE" --output none
done

# The licence travels with the version (#399).
echo "Uploading $VERSION/LICENSE"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file "$(dirname "$0")/../LICENSE" --name "$VERSION/LICENSE" --output none

echo "Uploading $VERSION/formats.json"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file "$INDEX" --name "$VERSION/formats.json" --output none

echo "Updating latest.json -> $VERSION"
POINTER=$(mktemp)
printf '{"version": "%s"}\n' "$VERSION" > "$POINTER"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file "$POINTER" --name "latest.json" --overwrite --output none
rm -f "$POINTER"

echo "Published formats@$VERSION and updated latest pointer."
