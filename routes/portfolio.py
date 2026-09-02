from flask import Blueprint, render_template
from flask_login import login_required

portfolio_bp = Blueprint("portfolio", __name__)


@portfolio_bp.route("/portfolio")
@login_required
def portfolio():
    return render_template("portfolio.html")
