from chronos.core.providers.factory import make_container
from chronos.core.settings import settings
from chronos.main.api.factory import APIFactory

container = make_container(settings=settings)
factory = APIFactory(container=container, settings=settings)
app = factory.make()
