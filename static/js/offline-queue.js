// offline-queue.js – handles offline order & payment queue

const OFFLINE_QUEUE_KEY = 'cafeteria-pos-offline-queue';
const SYNC_ENDPOINT = '/api/sync-offline/'; // we will create this endpoint later

// Save action to local queue
function queueOfflineAction(actionType, data) {
  let queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  queue.push({
    id: Date.now() + Math.random(),
    timestamp: new Date().toISOString(),
    type: actionType, // 'create_order', 'cash_payment', 'credit_sale'
    data: data,
    status: 'pending'
  });
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  showPendingBadge(queue.length);
}

// Show number of pending items in UI (call this on load)
function showPendingBadge(count) {
  const badge = document.getElementById('pending-sync-badge');
  if (badge) {
    badge.textContent = count > 0 ? count : '';
    badge.style.display = count > 0 ? 'inline-block' : 'none';
  }
}

// Try to sync when online
function trySync() {
  if (!navigator.onLine) return;

  let queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  if (queue.length === 0) return;

  // Send all pending items
  fetch(SYNC_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ actions: queue })
  })
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      // Clear synced items
      localStorage.removeItem(OFFLINE_QUEUE_KEY);
      showPendingBadge(0);
      alert('Offline actions synced successfully!');
    } else {
      console.error('Sync failed:', result.errors);
    }
  })
  .catch(err => console.error('Sync error:', err));
}

// Listen for online event
window.addEventListener('online', trySync);

// Run on load
document.addEventListener('DOMContentLoaded', () => {
  let queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  showPendingBadge(queue.length);
  trySync();
});

// Helper: get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}