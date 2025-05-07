from dishka import Provider, Scope, provide

from chronos.application.task_queue.run_service import EnqueueRunService
from chronos.infrastructure.task_queue.run_service import EnqueueRunServiceWithNats


class TaskQueueAdaptersProvider(Provider):
    scope = Scope.APP

    run_service = provide(EnqueueRunServiceWithNats, provides=EnqueueRunService)
