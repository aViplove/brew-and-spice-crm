// Brew & Spice — common UI helpers

// Sidebar toggle (mobile)
const menuBtn = document.getElementById('menuBtn');
const sidebar = document.getElementById('sidebar');
if (menuBtn && sidebar) {
  menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (window.innerWidth <= 720 &&
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !menuBtn.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// Date in topbar
const dateEl = document.getElementById('topbarDate');
if (dateEl) {
  const opts = { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' };
  dateEl.textContent = new Date().toLocaleDateString('en-IN', opts);
}

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.msg').forEach(m => {
    m.style.transition = 'opacity .4s';
    m.style.opacity = '0';
    setTimeout(() => m.remove(), 500);
  });
}, 5000);
