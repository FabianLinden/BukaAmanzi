from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.api.v1.endpoints.data_sync import initialize_data_sync_services
from app.core.config import settings
from app.db.session import init_db, async_session_factory
from app.db.seed import seed_database
from app.realtime.notifier import DataChangeNotifier
from app.websocket import create_websocket_router

logger = logging.getLogger(__name__)

# Mock Redis for local development
class MockRedis:
    async def publish(self, channel, message):
        logger.info(f"Mock Redis publish to {channel}: {message}")
    
    async def aclose(self):
        pass

class MockRedisPubSubListener:
    def __init__(self, redis_client, notifier):
        pass
    
    async def start_listening(self):
        # Mock listener that does nothing
        while True:
            await asyncio.sleep(60)  # Sleep indefinitely


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        
        # Use mock Redis for local development
        try:
            import redis.asyncio as redis
            app.state.redis = redis.from_url(settings.redis_url)
            from app.realtime.notifier import RedisPubSubListener
            redis_listener_class = RedisPubSubListener
            logger.info("Using real Redis connection")
        except Exception as e:
            logger.warning(f"Redis not available, using mock: {e}")
            app.state.redis = MockRedis()
            redis_listener_class = MockRedisPubSubListener
        
        app.state.notifier = DataChangeNotifier(app.state.redis)
        app.state.redis_listener_task = asyncio.create_task(
            redis_listener_class(app.state.redis, app.state.notifier).start_listening()
        )

        # seed demo data once
        async with async_session_factory() as session:
            try:
                ids = await seed_database(session)
                app.state.demo_ids = ids
                logger.info("Demo data seeded successfully")
            except Exception as e:
                logger.warning(f"Error seeding demo data: {e}")
                app.state.demo_ids = {}
        
        # Initialize data sync services
        try:
            initialize_data_sync_services(app.state.notifier)
            logger.info("Data sync services initialized")
        except Exception as e:
            logger.error(f"Error initializing data sync services: {e}")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        redis_task = getattr(app.state, "redis_listener_task", None)
        if redis_task:
            redis_task.cancel()
        redis_client = getattr(app.state, "redis", None)
        if redis_client:
            await redis_client.aclose()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(create_websocket_router())
    return app


app = create_app()

