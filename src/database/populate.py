import asyncio

from sqlalchemy import func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import UserGroupEnum, UserGroupModel, UserModel, get_db_contextmanager

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    """
    A class responsible for seeding the database from a CSV file using asynchronous SQLAlchemy.
    """

    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        """
        Initialize the seeder with the path to the CSV file and an async database session.

        :param csv_file_path: The path to the CSV file containing movie data.
        :param db_session: An instance of AsyncSession for performing database operations.
        """
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        """
        Check if the MovieModel table has at least one record.

        :return: True if there's already at least one movie in the database, otherwise False.
        """
        result = await self._db_session.execute(select(UserModel).limit(1))
        first_admin = result.scalars().first()
        return first_admin is not None

    async def _seed_test_users(self) -> None:
        print("======== Try to seed test users ========")
        result = await self._db_session.execute(select(func.count(UserModel.id)))
        user_count = result.scalar()

        if user_count and user_count > 0:
            print("Users already exist. Skipping user seeding.")
            return

        group_query = await self._db_session.execute(select(UserGroupModel))
        groups = {group.name.value: group.id for group in group_query.scalars()}

        user_data = [
            {
                "email": "admin@example.com",
                "password": "Admin123!",
                "group_id": groups.get("admin"),
            },
            {
                "email": "moderator@example.com",
                "password": "Moderator123!",
                "group_id": groups.get("moderator"),
            },
            {
                "email": "user@example.com",
                "password": "User123!",
                "group_id": groups.get("user"),
            },
        ]

        for data in user_data:
            user = UserModel.create(
                email=data["email"],
                raw_password=data["password"],
                group_id=data["group_id"],
            )
            user.is_active = True
            self._db_session.add(user)

        await self._db_session.commit()
        print("Default users seeded successfully.")

    async def seed(self) -> None:
        """
        Main method to seed the database with movie data from the CSV.
        It pre-processes the CSV, prepares reference data (countries, genres, actors, languages),
        inserts all movies, then inserts many-to-many relationships (genres, actors, languages).
        """
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            await self._seed_test_users()

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


async def main() -> None:
    """
    The main async entry point for running the database seeder.
    Checks if the database is already populated, and if not, performs the seeding process.
    """
    settings = get_settings()
    async with get_db_contextmanager() as db_session:
        seeder = CSVDatabaseSeeder(settings.PATH_TO_MOVIES_CSV, db_session)

        if not await seeder.is_db_populated():
            try:
                await seeder.seed()
                print("Database seeding completed successfully.")
            except Exception as e:
                print(f"Failed to seed the database: {e}")
        else:
            print("Database is already populated. Skipping seeding.")


if __name__ == "__main__":
    asyncio.run(main())
