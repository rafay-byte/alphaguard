// AlphaGuard AI - Dashboard: Scan Market button
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('scan-market-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    const progressWrap = document.getElementById('scan-progress');
    const fill = document.getElementById('scan-progress-fill');
    const label = document.getElementById('scan-progress-label');
    progressWrap.style.display = 'block';
    fill.style.width = '15%';
    label.textContent = 'Connecting to market data...';

    setTimeout(() => { fill.style.width = '55%'; label.textContent = 'Running quant + AI analysis...'; }, 500);

    try {
      const res = await fetch('/api/scan', { method: 'POST' });
      const data = await res.json();
      fill.style.width = '100%';
      label.textContent = `Scan complete - ${data.opportunities.length} assets evaluated.`;
      showToast(`Market scan complete: ${data.opportunities.length} opportunities found.`, 'SUCCESS');
      setTimeout(() => { window.location.href = '/opportunities'; }, 900);
    } catch (e) {
      label.textContent = 'Scan failed. Please try again.';
      btn.disabled = false;
    }
  });
});
