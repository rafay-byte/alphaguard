from flask import Blueprint, render_template
from flask_login import login_required

strategies_bp = Blueprint("strategies", __name__)


@strategies_bp.route("/strategy-lab")
@login_required
def strategy_lab():
    return render_template("strategy_lab.html")
