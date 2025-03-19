import click
from flask import Flask
from flask.cli import with_appcontext

from app import db
from app.utils import dat_to_database


@click.command("initdb")
@with_appcontext
def init_db_cmd():
    """解析 QQWRY 数据并导入到数据库"""

    db.drop_all()
    from app import models  # noqa

    db.create_all()
    dat_to_database(db)


def register_commands(app: Flask):
    app.cli.add_command(init_db_cmd)
