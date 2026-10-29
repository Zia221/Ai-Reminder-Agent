
from sqlalchemy import inspect, text

from app.db.session import engine


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_users_table_exists():
    inspector = inspect(engine)

    assert inspector.has_table("users")


def test_users_email_is_unique():
    inspector = inspect(engine)
    columns = inspector.get_unique_constraints("users")
    unique_column_sets = [
        set(constraint["column_names"])
        for constraint in columns
    ]

    indexes = inspector.get_indexes("users")
    unique_indexes = [
        set(index["column_names"])
        for index in indexes
        if index["unique"]
    ]

    assert {"email"} in unique_column_sets or {"email"} in unique_indexes
