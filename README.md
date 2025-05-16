# Chronos Crawler

1. Install

```sh
poetry install
# or
poetry update
```

For Windows OS, please install:

```sh
pip install python-magic-bin
```

And for Ubuntu based OS, you have to it by the bellow command:

```sh
sudo apt-get install libmagic1
```

1. Create `.env` file from `.env.example`

## Native

Run `chronos --help` to list out all available commands.

```sh
chronos --help
```

## Makefile

Run `make help` or just `make` to list out all available commands.

```sh
make help
```

## Pre-commit

```sh
pre-commit run --all-files
```
