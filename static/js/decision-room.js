// AlphaGuard AI - Decision Room: pipeline animation, confidence breakdown,
// bull/bear debate, risk matrix, "Why NOT Trade", and trade execution
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const tickerSelect = document.getElementById('ticker-select');
  const runBtn = document.getElementById('run-committee-btn');

  if (params.get('ticker')) tickerSelect.value = params.get('ticker');

  // Pipeline node animation
  const PIPELINE_AGENTS = ['market', 'quant', 'news', 'bull', 'bear', 'alternative', 'strategy', 'risk'];

  function setPipelineState(agentKey, state) {
    const node = document.querySelector(`.pipeline-node[data-agent="${agentKey}"]`);
    if (!node) return;
    node.classList.remove('analyzing', 'complete', 'rejected');
    if (state) node.classList.add(state);

    // Animate arrows
    const idx = PIPELINE_AGENTS.indexOf(agentKey);
    if (idx > 0) {
      const arrow = document.querySelector(`.pipeline-arrow[data-arrow="${idx - 1}"]`);
      if (arrow) {
        arrow.classList.remove('active', 'done');
        if (state === 'analyzing') arrow.classList.add('active');
        else if (state === 'complete') arrow.classList.add('done');
      }
    }
  }

  function resetPipeline() {
    PIPELINE_AGENTS.forEach(a => setPipelineState(a, ''));
    document.querySelectorAll('.pipeline-arrow').forEach(a => a.classList.remove('active', 'done'));
  }

  // Live socket-driven agent animation
  if (window.socket) {
    window.socket.on('agent_started', (data) => {
      setPipelineState(data.agent, 'analyzing');
      setAgentState(data.agent, 'analyzing');
      document.getElementById('agent-detail-panel').style.display = 'block';
    });
    window.socket.on('agent_completed', (data) => {
      const r = data.result || {};
      const text = r.reasoning || r.risks?.join(' ') || r.arguments?.join(' ') || 'Analysis complete.';
      setPipelineState(data.agent, 'complete');
      setAgentState(data.agent, 'complete', text);
    });
    window.socket.on('risk_check_started', () => {
      setPipelineState('risk', 'analyzing');
      setAgentState('risk', 'analyzing');
    });
    window.socket.on('risk_check_completed', (data) => {
      const state = data.result.approved ? 'complete' : 'rejected';
      setPipelineState('risk', state);
      setAgentState('risk', 'complete', (data.result.reasons || []).join(' '));
    });
  }

  async function runCommittee(ticker) {
    resetPipeline();
    resetAgentFlow();
    document.getElementById('confidence-wrap').innerHTML = '';
    document.getElementById('debate-wrap').innerHTML = '';
    document.getElementById('risk-matrix-wrap').innerHTML = '';
    document.getElementById('final-decision-wrap').innerHTML = '';
    document.getElementById('execution-wrap').innerHTML = '';
    document.getElementById('agent-detail-panel').style.display = 'none';
    runBtn.disabled = true;
    runBtn.textContent = 'Running committee...';

    const res = await runDecision(ticker);
    runBtn.disabled = false;
    runBtn.textContent = '🧠 Run Investment Committee';

    renderConfidenceBreakdown(ticker, res);
    renderBullBearDebate(res);
    renderRiskMatrix(res);
    renderFinalDecision(ticker, res);
  }

  // --- Confidence Breakdown ---
  function renderConfidenceBreakdown(ticker, res) {
    const decision = res.decision;
    const scores = decision.scores || {};
    const confidence = decision.confidence || 0;
    const wrap = document.getElementById('confidence-wrap');

    function barClass(val, key) {
      if (key === 'BULL') return 'bull';
      if (key === 'BEAR') return 'bear';
      if (val >= 70) return 'high';
      if (val >= 45) return 'medium';
      return 'low';
    }

    const scoreRows = Object.entries(scores).map(([key, val]) => `
      <div class="score-row">
        <div class="score-label">${key.charAt(0) + key.slice(1).toLowerCase()} Score</div>
        <div class="score-bar-track"><div class="score-bar-fill ${barClass(val, key)}" style="width:${Math.min(100, val)}%"></div></div>
        <div class="score-value">${Math.round(val)}%</div>
      </div>
    `).join('');

    const actionClass = decision.final_decision === 'BUY' ? 'buy' :
      (decision.final_decision === 'HOLD' ? 'hold' : 'no-trade');

    wrap.innerHTML = `
      <div class="confidence-breakdown slide-up">
        <div class="cb-title">AlphaGuard Investment Committee · ${ticker}</div>
        ${scoreRows}
        <div class="composite-score-section">
          <div>
            <div class="composite-label">Composite Score</div>
            <div class="composite-value">${Math.round(confidence)}%</div>
          </div>
          <div>
            <div class="composite-label">Decision</div>
            <div class="composite-decision ${actionClass}">${decision.final_decision}</div>
          </div>
        </div>
      </div>
    `;
  }

  // --- Bull vs Bear Debate ---
  function renderBullBearDebate(res) {
    const decision = res.decision;
    const bullSummary = decision.bull_summary || 'No bull thesis available.';
    const bearSummary = decision.bear_summary || 'No bear concerns identified.';
    const wrap = document.getElementById('debate-wrap');

    wrap.innerHTML = `
      <div class="debate-row slide-up">
        <div class="debate-card bull">
          <div class="debate-header">
            <div class="debate-icon">🟢</div>
            <div class="debate-title">Bull Agent</div>
          </div>
          <div class="debate-text">${bullSummary}</div>
        </div>
        <div class="debate-card bear">
          <div class="debate-header">
            <div class="debate-icon">🔴</div>
            <div class="debate-title">Bear Agent</div>
          </div>
          <div class="debate-text">${bearSummary}</div>
        </div>
      </div>
    `;
  }

  // --- Risk Matrix ---
  function renderRiskMatrix(res) {
    const risk = res.risk;
    if (!risk) return;
    const wrap = document.getElementById('risk-matrix-wrap');
    const checks = risk.checks || [];
    const passed = risk.passed_count || 0;
    const total = risk.total_checks || 0;

    const checkItems = checks.map(c => `
      <div class="risk-check-item">
        <div class="risk-check-icon ${c.passed ? 'pass' : 'fail'}">${c.passed ? '✓' : '✕'}</div>
        <div class="risk-check-name">${c.name}</div>
        <div class="risk-check-detail">${c.detail}</div>
      </div>
    `).join('');

    wrap.innerHTML = `
      <div class="risk-matrix slide-up">
        <div class="rm-title">🛡️ Deterministic Risk Engine</div>
        ${checkItems}
        <div class="risk-matrix-summary">
          <div class="rm-count">${passed} / ${total} PASSED</div>
          <div class="rm-verdict ${risk.approved ? 'approved' : 'rejected'}">
            ${risk.approved ? 'EXECUTION AUTHORIZED' : 'TRADE BLOCKED'}
          </div>
        </div>
      </div>
    `;
  }

  // --- Final Decision + Why NOT Trade ---
  function renderFinalDecision(ticker, res) {
    const decision = res.decision;
    const risk = res.risk;
    const wrap = document.getElementById('final-decision-wrap');

    const actionClass = decision.final_decision === 'BUY' ? 'buy' :
      (decision.final_decision === 'HOLD' ? 'hold' : 'no-trade');

    let html = `
      <div class="glass-panel final-decision-card slide-up">
        <div style="font-size:12px; letter-spacing:0.06em; color:var(--text-tertiary); text-transform:uppercase;">Final Committee Decision</div>
        <div class="final-decision-action ${actionClass}">${decision.final_decision} ${ticker}</div>
        <div style="margin: 10px auto; max-width:420px;">
          <div class="confidence-meter"><div class="confidence-fill" style="width:${decision.confidence}%;"></div></div>
          <div style="font-size:12.5px; color:var(--text-secondary); margin-top:6px;">Confidence ${Math.round(decision.confidence)}%</div>
        </div>
    `;

    // --- "Why NOT Trade?" card ---
    if (decision.final_decision !== 'BUY' && decision.hold_reasons && decision.hold_reasons.length > 0) {
      const reasons = decision.hold_reasons.map(r =>
        `<div class="wnc-reason"><span class="wnc-dot">▸</span> ${r}</div>`
      ).join('');

      html += `
        <div class="why-not-card mt-16" style="text-align:left; max-width:540px; margin-left:auto; margin-right:auto;">
          <div class="wnc-header">
            <span style="font-size:18px;">⚠️</span>
            <div class="wnc-title">Why Not Trade?</div>
          </div>
          <div class="wnc-subtitle">The committee analyzed ${ticker} but decided not to enter a position.</div>
          ${reasons}
        </div>
      `;
    }

    // Risk result — blocked by risk engine
    if (risk && !risk.approved) {
      const failedChecks = (risk.checks || []).filter(c => !c.passed);
      const failedHtml = failedChecks.map(c =>
        `<div class="wnc-reason"><span class="wnc-dot" style="color:var(--danger);">✕</span> <strong>${c.name}:</strong> ${c.detail}</div>`
      ).join('');

      html += `
        <div class="why-not-card mt-16" style="text-align:left; max-width:540px; margin-left:auto; margin-right:auto; background:rgba(217,79,79,0.06); border-color:rgba(217,79,79,0.2);">
          <div class="wnc-header">
            <span style="font-size:18px;">🛡️</span>
            <div class="wnc-title" style="color:var(--danger);">Risk Engine Blocked This Trade</div>
          </div>
          <div class="wnc-subtitle">The AI wanted to trade, but the deterministic Risk Engine blocked it.</div>
          ${failedHtml}
        </div>
      `;
    }

    // Execute button (only if approved)
    if (risk && risk.approved && decision.proposal) {
      html += `
        <div class="mt-24">
          <span class="badge badge-success" style="font-size:13px; padding:8px 18px;">
            RISK APPROVED · ${risk.passed_count}/${risk.total_checks} CHECKS PASSED
          </span>
        </div>
        <button class="btn btn-primary btn-press mt-16" id="execute-trade-btn">⚡ Execute Paper Trade</button>
      `;
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
