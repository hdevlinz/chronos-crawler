from chronos.core.settings import Settings


class EnqueuesWithNats:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_nats_url(self) -> str:
        assert self._settings.nats_url is not None, "NATS URL is not configured"
        return self._settings.nats_url
