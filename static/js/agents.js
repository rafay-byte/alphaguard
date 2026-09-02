// AlphaGuard AI - agent status widget helpers (used by decision-room.js)
const AGENT_LABELS = {
  market: 'Market Analyst', quant: 'Quant Analyst', news: 'News Intelligence',
  bull: 'Bull Agent', bear: 'Bear Agent', alternative: 'Alternative Agent',
  strategy: 'Strategy Agent', risk: 'Risk Engine',
};

function setAgentState(agentKey, state, reasoningText) {
  const card = document.querySelector(`.agent-card[data-agent="${agentKey}"]`);
  if (!card) return;
  card.classList.remove('analyzing', 'complete');
  const label = card.querySelector('.agent-status-label');
  const reasoning = card.querySelector('.agent-reasoning');

  if (state === 'analyzing') {
    card.classList.add('analyzing');
    label.textContent = 'ANALYZING';
    label.className = 'agent-status-label analyzing';
    reasoning.innerHTML = '<span class="agent-spinner"></span> Analyzing...';
  } else if (state === 'complete') {
    card.classList.add('complete');
    label.textContent = 'COMPLETE';
    label.className = 'agent-status-label complete';
    if (reasoningText) reasoning.textContent = reasoningText;
  } else {
    label.textContent = 'WAITING';
    label.className = 'agent-status-label waiting';
    reasoning.textContent = 'Awaiting analysis...';
  }
}

function resetAgentFlow() {
  Object.keys(AGENT_LABELS).forEach(k => setAgentState(k, 'waiting'));
}
