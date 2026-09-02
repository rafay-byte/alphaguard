// AlphaGuard AI - shared trading helpers used across pages
async function runDecision(ticker) {
  const res = await fetch(`/api/decision/${ticker}`, { method: 'POST' });
  return res.json();
}

async function submitTrade(proposal) {
  const res = await fetch('/api/trade', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proposal })
  });
  return res.json();
}
