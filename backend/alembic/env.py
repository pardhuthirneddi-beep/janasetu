from logging.config import fileConfig

from alembic import context

from app.main import Base, engine, settings

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", str(engine.url).replace("%", "%%"))
target_metadata = Base.metadata


def offline():
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def online():
    # Reuse the URL already normalized by the application (mysql+pymysql://),
    # rather than Alembic's default mysql+mysqldb DBAPI.
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    offline()
else:
    online()
