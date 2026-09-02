"""News Intelligence Agent."""


def run_news_agent(ticker, news_service):
    context = news_service.get_news_context(ticker)
    context["score"] = context["sentiment_score"]
    context["reasoning"] = (
        f"Sentiment score {context['sentiment_score']}/100 based on "
        f"{len(context['positive_factors'])} positive and {len(context['negative_factors'])} "
        f"negative factors." + (" (DEMO MODE - no live news feed configured)" if context["demo_mode"] else "")
    )
    return context
