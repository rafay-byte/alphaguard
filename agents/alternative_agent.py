"""Alternative Opportunity Agent - is this really the best trade available?"""


def run_alternative_agent(candidate_scores, threshold=60):
    """candidate_scores: dict {ticker: overall_score}"""
    if not candidate_scores:
        return {"best_opportunity": None, "candidates": {}, "reasoning": "No candidates scanned."}

    best_ticker = max(candidate_scores, key=candidate_scores.get)
    best_score = candidate_scores[best_ticker]

    if best_score < threshold:
        return {
            "best_opportunity": None,
            "candidates": candidate_scores,
            "reasoning": f"No monitored asset clears the minimum opportunity threshold of {threshold}. "
                         f"Best candidate {best_ticker} scored only {best_score}.",
        }

    return {
        "best_opportunity": best_ticker,
        "candidates": candidate_scores,
        "reasoning": f"{best_ticker} scored highest among {len(candidate_scores)} monitored assets "
                     f"at {best_score}, clearing the {threshold} opportunity threshold.",
    }
