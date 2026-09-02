def test_app_boots_in_demo_mode(app):
    assert app.config["DEMO_MODE"] is True


def test_alpaca_service_demo_account():
    from broker.client import alpaca_service
    with __import__("app").create_app().app_context():
        account = alpaca_service.get_account()
        assert account["equity"] > 0
