from faststream.nats import NatsRoute, NatsRouter

from chronos.presentation.workers.run_service import run_service

router = NatsRouter(
    handlers=[
        NatsRoute(
            call=run_service,
            subject="run_service",
            queue="chronos_queue",
            max_workers=1,
        ),
    ],
)
