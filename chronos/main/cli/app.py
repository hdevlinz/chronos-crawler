from chronos.main.cli.factory import CLIFactory


def run_cli() -> None:
    factory = CLIFactory()
    app = factory.make()
    app()
