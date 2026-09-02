from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models.trade import Trade

trading_bp = Blueprint("trading", __name__)


@trading_bp.route("/trade/<int:trade_id>")
@login_required
def trade_detail(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.user_id != current_user.id:
        abort(403)
    return render_template("trade_detail.html", trade=trade)
