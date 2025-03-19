from flask import Blueprint, abort, jsonify, render_template, request
from sqlalchemy import select

from app.extensions import db
from app.models import IPData
from app.utils import int_ip_to_str, str_ip_to_int

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    ip_address = request.remote_addr
    return render_template("index.html", ip_address=ip_address)


@main_bp.route("/api/ip/<ip>", methods=["GET"])
def get_ip_info(ip: str):
    try:
        ip_num = str_ip_to_int(ip)
    except ValueError:
        abort(400, description="Invalid IP address format")

    stmt = (
        select(IPData)
        .where(IPData.ip_start_num <= ip_num)
        .where(IPData.ip_end_num >= ip_num)
        .order_by(IPData.ip_end_num - IPData.ip_start_num)  # 优先匹配最小范围
        .limit(1)
    )

    if (ip_data := db.session.execute(stmt).scalars().first()) is None:
        abort(404, description="IP address information not found")

    return jsonify(
        {
            "ip": ip,
            "location": ip_data.location,
            "info": ip_data.info,
            "ip_range": {"start": int_ip_to_str(ip_data.ip_start_num), "end": int_ip_to_str(ip_data.ip_end_num)},
        }
    )
