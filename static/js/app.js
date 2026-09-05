/**
 * DentiFlow - Global Application Core Script
 * Handles Toast system, Global Search (Ctrl+K), Sidebar Collapse, Audio Chimes, Branch Switcher
 */

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initGlobalSearch();
  initKeyboardShortcuts();
});

// 1. Toast Notification System
window.showToast = function(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `df-toast toast-${type} animate-slide-right`;
  
  let iconClass = 'fa-circle-check text-success';
  if (type === 'warning') iconClass = 'fa-triangle-exclamation text-warning';
  else if (type === 'danger') iconClass = 'fa-circle-exclamation text-danger';
  else if (type === 'info') iconClass = 'fa-circle-info text-primary';

  toast.innerHTML = `
    <i class="fa-solid ${iconClass}" style="font-size: 18px;"></i>
    <div style="flex: 1; font-size: 13.5px; font-weight: 500;">${message}</div>
    <button type="button" class="btn-close" style="font-size: 10px;" onclick="this.parentElement.remove()"></button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

// 2. Audio Chime Simulator (for Queue calling & success cues)
window.playChime = function(type = 'bell') {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    if (type === 'bell') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.25, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
      osc.start();
      osc.stop(ctx.currentTime + 0.8);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
      osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1); // E5
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    }
  } catch (e) {
    console.log('Audio cue simulated (AudioContext unavailable).');
  }
};

// 3. Sidebar Collapse & Responsive Drawer
function initSidebar() {
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('app-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('mobile-open');
      } else {
        sidebar.classList.toggle('collapsed');
      }
    });
  }

  // Highlight active nav item
  const currentPath = window.location.pathname;
  document.querySelectorAll('.app-sidebar .nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
      item.classList.add('active');
    }
  });
}

// 4. Global Quick Search Modal (Ctrl+K / Cmd+K)
function initGlobalSearch() {
  const searchModal = document.getElementById('global-search-modal');
  const searchInput = document.getElementById('global-search-input');
  const searchBarTop = document.getElementById('topbar-search-trigger');

  function openSearch() {
    if (searchModal) {
      searchModal.style.display = 'flex';
      if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
        filterSearchResults('');
      }
    }
  }

  function closeSearch() {
    if (searchModal) searchModal.style.display = 'none';
  }

  if (searchBarTop) searchBarTop.addEventListener('click', openSearch);
  
  if (searchModal) {
    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal) closeSearch();
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      filterSearchResults(e.target.value.trim().toLowerCase());
    });
  }

  window.openGlobalSearch = openSearch;
  window.closeGlobalSearch = closeSearch;
}

function filterSearchResults(query) {
  const resultsContainer = document.getElementById('global-search-results');
  if (!resultsContainer) return;

  const demoItems = [
    { title: 'Aravind', category: 'Patient', sub: 'DF-2026-001 • Tooth #16 review', url: '/patients/1', icon: 'fa-user' },
    { title: 'Vishal', category: 'Patient', sub: 'DF-2026-002 • Scaling follow-up', url: '/patients/2', icon: 'fa-user' },
    { title: 'Medha', category: 'Patient', sub: 'DF-2026-003 • Pediatric review', url: '/patients/3', icon: 'fa-user' },
    { title: 'Dr. Ananya Sharma', category: 'Doctor', sub: 'Chief Endodontist • Chair 01', url: '/staff', icon: 'fa-user-doctor' },
    { title: 'Root Canal Treatment (Tooth #16)', category: 'Appointment', sub: 'Today 09:00 AM • Aravind', url: '/appointments', icon: 'fa-calendar-check' },
    { title: 'INV-2026-1029 (₹17,110)', category: 'Invoice', sub: 'Aravind • Partial Paid', url: '/billing', icon: 'fa-receipt' },
    { title: '3M Filtek Composite Resin A2', category: 'Inventory', sub: '6 syringes remaining (Low Stock)', url: '/inventory', icon: 'fa-boxes-stacked' },
    { title: 'Dental Operatory Chair 01', category: 'Equipment', sub: 'Operational • Anthos A3 Plus', url: '/operations', icon: 'fa-chair' }
  ];

  const filtered = query ? demoItems.filter(i => i.title.toLowerCase().includes(query) || i.sub.toLowerCase().includes(query) || i.category.toLowerCase().includes(query)) : demoItems;

  if (filtered.length === 0) {
    resultsContainer.innerHTML = `
      <div class="text-center py-4 text-muted">
        <i class="fa-solid fa-magnifying-glass mb-2" style="font-size: 24px; opacity: 0.4;"></i>
        <p class="mb-0">No matching records found for "${query}"</p>
      </div>
    `;
    return;
  }

  resultsContainer.innerHTML = filtered.map(item => `
    <div class="search-result-item" onclick="window.location.href='${item.url}'">
      <div class="kpi-icon-box kpi-icon-blue" style="width: 36px; height: 36px; font-size: 15px;">
        <i class="fa-solid ${item.icon}"></i>
      </div>
      <div style="flex: 1;">
        <div class="d-flex align-items-center justify-content-between">
          <span style="font-weight: 600; font-size: 14px;">${item.title}</span>
          <span class="badge bg-light text-dark border" style="font-size: 10px;">${item.category}</span>
        </div>
        <div class="text-muted" style="font-size: 12px;">${item.sub}</div>
      </div>
    </div>
  `).join('');
}

// 5. Global Keyboard Shortcuts
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (window.openGlobalSearch) window.openGlobalSearch();
    }
    if (e.key === 'Escape') {
      if (window.closeGlobalSearch) window.closeGlobalSearch();
    }
  });
}

// 6. Branch Switcher Helper
window.switchClinicBranch = async function(branchId, branchName) {
  try {
    const res = await fetch(`/api/branches/switch/${branchId}`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Active clinic set to ${branchName}`, 'success');
      setTimeout(() => window.location.reload(), 500);
    }
  } catch (err) {
    console.error(err);
  }
};
