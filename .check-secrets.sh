#!/bin/bash
if [ -x .check-secrets-impl.sh ]; then
    . .check-secrets-impl.sh
elif [ -f .check-secrets-impl.sh ]; then
    exit 1
else
    exit 0
fi
