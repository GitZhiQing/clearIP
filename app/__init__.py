from flask import Flask

from app.config import config
from app.extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    # 注册命令行命令
    from app.commands import register_commands

    register_commands(app)

    # 注册上下文处理器
    from app.utils import inject_env_vars

    app.context_processor(inject_env_vars)

    # 注册蓝图
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
