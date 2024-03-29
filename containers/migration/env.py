#!/usr/bin/env python3
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import attributes.main as service_atribute_authority
import entitlements.main as entitlements
import entitlement_store.main as entitlement_store


sys.path.append(os.getcwd())
sys.path.append("../")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

section = config.config_ini_section
config.set_section_option(
    section, "POSTGRES_USER", str(entitlement_store.POSTGRES_USER)
)
config.set_section_option(
    section, "POSTGRES_PASSWORD", str(entitlement_store.POSTGRES_PASSWORD)
)
config.set_section_option(
    section, "POSTGRES_DATABASE", str(entitlement_store.POSTGRES_DATABASE)
)
config.set_section_option(
    section, "POSTGRES_HOST", str(entitlement_store.POSTGRES_HOST)
)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = [
    service_atribute_authority.metadata,
    entitlements.metadata,
    entitlement_store.metadata,
]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migration in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migration in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
