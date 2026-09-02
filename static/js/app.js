// AlphaGuard AI - Global app helpers (number count-up animation, etc.)
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.count-up').forEach(el => {
    const target = parseFloat(el.dataset.value);
    if (isNaN(target)) return;
    const isCurrency = el.textContent.trim().startsWith('$');
    let current = 0;
    const steps = 30;
    const increment = target / steps;
    let i = 0;
    const timer = setInterval(() => {
      i++;
      current += increment;
      if (i >= steps) { current = target; clearInterval(timer); }
      el.textContent = (isCurrency ? '$' : '') + current.toFixed(2);
    }, 16);
  });
});
