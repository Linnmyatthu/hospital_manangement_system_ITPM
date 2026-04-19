document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const refreshBtn = document.getElementById('refreshBtn');
  const lastUpdate = document.getElementById('lastUpdate');
  const feedList = document.getElementById('feedList');

  // mobile sidebar toggle
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      const isHidden = window.getComputedStyle(sidebar).display === 'none';
      sidebar.style.display = isHidden ? 'flex' : 'none';
    });
  }

  // sample new activities
  const sampleActivities = [
    {
      type: 'admission',
      time: '13:45',
      patient: 'Thomas Wright',
      age: '45M',
      ward: 'CCU Bay 1',
      diagnosis: 'Acute MI',
      doctor: 'Dr. N. Khan'
    },
    {
      type: 'discharge',
      time: '13:42',
      patient: 'Patricia White',
      age: '66F',
      ward: 'AMU Bay 1',
      stay: '6 days'
    },
    {
      type: 'treatment',
      time: '13:38',
      patient: 'David Wilson',
      treatment: 'ECG',
      ward: 'AMU Bay 5',
      doctor: 'Dr. R. Morgan'
    },
    {
      type: 'alert',
      time: '13:35',
      message: 'ICU capacity reached 92%',
      meta: 'Warning threshold exceeded'
    }
  ];

  // add new activity to feed
  function addActivity(activity) {
    const item = document.createElement('div');
    item.className = `feed-item ${activity.type}-item`;

    let badgeClass = '';
    let badgeText = '';
    let content = '';

    if (activity.type === 'admission') {
      badgeClass = 'admission-badge';
      badgeText = 'Admission';
      content = `<p class="feed-text"><strong>${activity.patient}</strong> (${activity.age}) admitted to <strong>${activity.ward}</strong></p><p class="feed-meta">${activity.diagnosis} • ${activity.doctor}</p>`;
    } else if (activity.type === 'discharge') {
      badgeClass = 'discharge-badge';
      badgeText = 'Discharge';
      content = `<p class="feed-text"><strong>${activity.patient}</strong> (${activity.age}) discharged from <strong>${activity.ward}</strong></p><p class="feed-meta">Length of stay: ${activity.stay}</p>`;
    } else if (activity.type === 'treatment') {
      badgeClass = 'treatment-badge';
      badgeText = 'Treatment';
      content = `<p class="feed-text"><strong>${activity.patient}</strong> received <strong>${activity.treatment}</strong></p><p class="feed-meta">${activity.ward} • ${activity.doctor}</p>`;
    } else if (activity.type === 'alert') {
      badgeClass = 'alert-badge';
      badgeText = 'Alert';
      content = `<p class="feed-text"><strong>${activity.message}</strong></p><p class="feed-meta">${activity.meta}</p>`;
    }

    item.innerHTML = `
      <div class="feed-time">${activity.time}</div>
      <div class="feed-content">
        <div class="feed-badge ${badgeClass}">${badgeText}</div>
        ${content}
      </div>
    `;

    if (feedList) {
      feedList.insertBefore(item, feedList.firstChild);
      
      // fade in animation
      item.style.opacity = '0';
      setTimeout(() => {
        item.style.transition = 'opacity 0.3s';
        item.style.opacity = '1';
      }, 10);
    }
  }

  // refresh button - add random activity
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      const randomActivity = sampleActivities[Math.floor(Math.random() * sampleActivities.length)];
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      randomActivity.time = `${hours}:${minutes}`;
      
      addActivity(randomActivity);
      
      // update last update time
      if (lastUpdate) {
        lastUpdate.textContent = 'just now';
      }

      // increment admission/discharge counters
      if (randomActivity.type === 'admission') {
        const admCount = document.getElementById('admissionsCount');
        if (admCount) {
          const current = parseInt(admCount.textContent);
          admCount.textContent = current + 1;
        }
      } else if (randomActivity.type === 'discharge') {
        const dischCount = document.getElementById('dischargesCount');
        if (dischCount) {
          const current = parseInt(dischCount.textContent);
          dischCount.textContent = current + 1;
        }
      } else if (randomActivity.type === 'alert') {
        const alertCount = document.getElementById('alertsCount');
        if (alertCount) {
          const current = parseInt(alertCount.textContent);
          alertCount.textContent = current + 1;
        }
      }
    });
  }

  // auto-refresh every 30 seconds (optional)
  setInterval(() => {
    if (lastUpdate) {
      const now = new Date();
      lastUpdate.textContent = 'just now';
    }
  }, 30000);
});
