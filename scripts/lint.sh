#!/usr/bin/env bash

set -x

ruff check chronos
mypy chronos

black chronos --check
