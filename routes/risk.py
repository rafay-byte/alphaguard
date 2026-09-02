from flask import Blueprint, render_template
from flask_login import login_required

risk_bp = Blueprint("risk", __name__)


@risk_bp.route("/risk")
@login_required
def risk_center():
    return render_template("risk_center.html")


@risk_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")
