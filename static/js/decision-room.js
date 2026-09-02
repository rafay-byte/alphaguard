// AlphaGuard AI - Decision Room: runs the committee, animates agents, executes trades
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const tickerSelect = document.getElementById('ticker-select');
  const runBtn = document.getElementById('run-committee-btn');

  if (params.get('ticker')) tickerSelect.value = params.get('ticker');

  // Live socket-driven agent animation
  if (window.socket) {
    window.socket.on('agent_started', (data) => setAgentState(data.agent, 'analyzing'));
    window.socket.on('agent_completed', (data) => {
      const r = data.result || {};
      const text = r.reasoning || r.risks?.join(' ') || r.arguments?.join(' ') || 'Analysis complete.';
      setAgentState(data.agent, 'complete', text);
    });
    window.socket.on('risk_check_started', () => setAgentState('risk', 'analyzing'));
    window.socket.on('risk_check_completed', (data) => {
      setAgentState('risk', 'complete', (data.result.reasons || []).join(' '));
    });
  }

  async function runCommittee(ticker) {
    resetAgentFlow();
    document.getElementById('final-decision-wrap').innerHTML = '';
    document.getElementById('execution-wrap').innerHTML = '';
    runBtn.disabled = true;
    runBtn.textContent = 'Running committee...';

    const res = await runDecision(ticker);
    runBtn.disabled = false;
    runBtn.textContent = '🧠 Run Investment Committee';

    renderFinalDecision(ticker, res);
  }

  function renderFinalDecision(ticker, res) {
    const decision = res.decision;
    const risk = res.risk;
    const wrap = document.getElementById('final-decision-wrap');

    const actionClass = decision.final_decision === 'BUY' ? 'buy' :
      (decision.final_decision === 'HOLD' ? 'hold' : 'no-trade');

    let html = `
      <div class="glass-panel final-decision-card slide-up">
        <div style="font-size:12px; letter-spacing:0.06em; color:var(--text-tertiary); text-transform:uppercase;">AI Investment Committee Decision</div>
        <div class="final-decision-action ${actionClass}">${decision.final_decision} ${ticker}</div>
        <div style="margin: 10px auto; max-width:420px;">
          <div class="confidence-meter"><div class="confidence-fill" style="width:${decision.confidence}%;"></div></div>
          <div style="font-size:12.5px; color:var(--text-secondary); margin-top:6px;">Confidence ${decision.confidence}%</div>
        </div>
        <p style="max-width:520px; margin:14px auto 0; font-size:13.5px; color:var(--text-secondary);">${decision.reasoning}</p>
    `;

    if (risk) {
      const badgeClass = risk.approved ? 'badge-success' : 'badge-danger';
      html += `
        <div class="mt-24">
          <span class="badge ${badgeClass}" style="font-size:13px; padding:8px 18px;">
            ${risk.approved ? 'RISK APPROVED' : 'RISK REJECTED'}
          </span>
          <div style="text-align:left; max-width:480px; margin:14px auto 0; font-size:12.5px; color:var(--text-secondary);">
            ${risk.reasons.map(r => `<div>• ${r}</div>`).join('')}
          </div>
        </div>
      `;
      if (risk.approved && decision.proposal) {
        html += `<button class="btn btn-primary btn-press mt-16" id="execute-trade-btn">Execute Paper Trade</button>`;
      }
    }
    html += `</div>`;
    wrap.innerHTML = html;

    const execBtn = document.getElementById('execute-trade-btn');
    if (execBtn) {
      execBtn.addEventListener('click', () => executeTrade(decision.proposal));
    }
  }

  async function executeTrade(proposal) {
    const execWrap = document.getElementById('execution-wrap');
    const steps = ['AI DECISION', 'RISK APPROVED', 'ORDER CREATED', 'SENT TO ALPACA', 'ORDER FILLED', 'POSITION ACTIVE'];
    execWrap.innerHTML = `
      <div class="glass-panel card mt-16 slide-up">
        <div class="card-title">Trade Execution</div>
        <div class="exec-timeline" id="exec-timeline">
          ${steps.map(s => `<div class="exec-step" data-step="${s}"><div class="exec-dot"></div><div><div class="exec-label">${s}</div><div class="exec-time"></div></div></div>`).join('')}
        </div>
      </div>
    `;

    const markDone = (label) => {
      const step = document.querySelector(`.exec-step[data-step="${label}"]`);
      if (step) {
        step.classList.remove('active');
        step.classList.add('done');
        step.querySelector('.exec-time').textContent = new Date().toLocaleTimeString();
      }
    };
    const markActive = (label) => {
      const step = document.querySelector(`.exec-step[data-step="${label}"]`);
      if (step) step.classList.add('active');
    };

    markActive('AI DECISION'); await sleep(300); markDone('AI DECISION');
    markActive('RISK APPROVED'); await sleep(300); markDone('RISK APPROVED');
    markActive('ORDER CREATED'); await sleep(300); markDone('ORDER CREATED');
    markActive('SENT TO ALPACA');

    const result = await submitTrade(proposal);

    if (result.error) {
      showToast(result.error, 'CRITICAL');
      return;
    }

    markDone('SENT TO ALPACA');
    markActive('ORDER FILLED'); await sleep(250); markDone('ORDER FILLED');
    markActive('POSITION ACTIVE'); await sleep(250); markDone('POSITION ACTIVE');

    showToast(`Trade executed: ${result.trade.action} ${result.trade.quantity} ${result.trade.ticker}`, 'SUCCESS');
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  runBtn.addEventListener('click', () => runCommittee(tickerSelect.value));

  if (params.get('auto') === '1') {
    runCommittee(tickerSelect.value);
  }
});
