// AlphaGuard AI - Toast notification system + shared Socket.IO connection
window.socket = (typeof io !== 'undefined') ? io() : null;

function showToast(message, severity) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const colors = { SUCCESS: '#17a673', CRITICAL: '#d94f4f', WARNING: '#c9891f', INFO: '#5b5fef' };
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.borderLeft = `3px solid ${colors[severity] || colors.INFO}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

if (window.socket) {
  window.socket.on('notification', (data) => showToast(data.message, data.severity));
}
