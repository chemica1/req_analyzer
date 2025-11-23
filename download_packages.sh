#!/bin/bash
set -e

mkdir -p packages

echo "Building PyPika wheel locally (workaround for missing Linux wheel)..."
pip wheel PyPika -w packages

echo "Downloading Linux packages to ./packages..."
# Download wheels for Linux (manylinux) to ensure compatibility
# We use --platform manylinux2014_x86_64 to target standard Linux
# If your target is ARM Linux, change to manylinux2014_aarch64
# Assuming x86_64 for general Linux servers. If user is on ARM Mac, we need to be careful.
# Safest is to download for the target architecture. I'll assume x86_64 (Intel/AMD) as it's most common for servers.
# If the user is deploying to a Raspberry Pi or ARM server, they need to tell us.

pip download \
    --dest packages \
    --only-binary=:all: \
    --find-links packages \
    --platform manylinux2014_x86_64 \
    --python-version 3.10 \
    --implementation cp \
    --abi cp310 \
    -r requirements.txt

echo "Download complete. Please commit the 'packages' folder to Git."
