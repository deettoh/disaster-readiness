"""RQ worker bootstrap entrypoint."""

import os

from redis import Redis
from rq import Queue, Worker


def main() -> None:
    """Start an RQ worker using environment configured Redis/queue settings."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_name = os.getenv("QUEUE_NAME", "image-processing")

    redis_connection = Redis.from_url(redis_url)
    queue = Queue(name=queue_name, connection=redis_connection)
    worker = Worker(queues=[queue], connection=redis_connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
