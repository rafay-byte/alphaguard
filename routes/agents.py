from flask import Blueprint, render_template
from flask_login import login_required

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/decision-room")
@login_required
def decision_room():
    return render_template("decision_room.html")


@agents_bp.route("/opportunities")
@login_required
def opportunities():
    return render_template("opportunities.html")


@agents_bp.route("/journal")
@login_required
def journal():
    return render_template("journal.html")
