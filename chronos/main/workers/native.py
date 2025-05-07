from chronos.core.providers.factory import make_container
from chronos.core.settings import settings
from chronos.main.workers.factory import WorkerFactory

container = make_container(settings=settings)
factory = WorkerFactory(container=container, settings=settings)
worker = factory.make()
