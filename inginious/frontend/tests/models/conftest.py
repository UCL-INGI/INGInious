import pytest
import pytest_asyncio
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from inginious.frontend.models.user import User


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def current_loop():
    return asyncio.get_running_loop()


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def test_db(current_loop):
    """
    Initialize a test database and clear it after tests.
    """
    # Defining Motor client
    motor_client = AsyncIOMotorClient(host="localhost")

    # Creating database if it does not exist and initializing Beanie
    beanie_database = motor_client.get_database("INGInious_beanie_tests")
    await init_beanie(
        database=beanie_database,
        document_models=[User]
    )

    yield beanie_database

    # Cleanup after tests
    await motor_client.drop_database("INGInious_beanie_tests")
    motor_client.close()