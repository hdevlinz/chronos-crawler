#!/usr/bin/env bash

set -x

ruff format chronos

ruff check chronos --select I --fix

black --skip-string-normalization chronos
