document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const refreshBtn = document.getElementById('refreshBtn');
  const lastUpdate = document.getElementById('lastUpdate');
  const feedList = document.getElementById('feedList');
  const wardList = document.getElementById('wardList');

  const admissionsEl = document.getElementById('admissionsCount');
  const dischargesEl = document.getElementById('dischargesCount');
  const alertsEl = document.getElementById('alertsCount');
  const staffEl = document.getElementById('staffCount');

  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      const isHidden = window.getComputedStyle(sidebar).display === 'none';
      sidebar.style.display = isHidden ? 'flex' : 'none';
    });
  }

  function getUKTimeString(date) {
    return date.toLocaleTimeString('en-GB', {
      timeZone: 'Europe/London',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  }

  async function refreshLiveData() {
    try {
      const statsRes = await fetch('/api/live/stats');
      const stats = await statsRes.json();
      admissionsEl.textContent = stats.admissions_today;
      dischargesEl.textContent = stats.discharges_today;
      alertsEl.textContent = stats.critical_alerts;
      staffEl.textContent = stats.staff_on_duty;

      const feedRes = await fetch('/api/live/feed');
      const activities = await feedRes.json();
      feedList.innerHTML = '';

      if (activities.length === 0) {
        const emptyItem = document.createElement('div');
        emptyItem.className = 'feed-item';
        emptyItem.innerHTML = '<p class="feed-text">No recent activity today</p>';
        feedList.appendChild(emptyItem);
      } else {
        activities.forEach(act => {
          const item = document.createElement('div');
          item.className = `feed-item ${act.type}-item`;

          let badgeClass = '';
          let badgeText = '';

          switch (act.type) {
            case 'admission':
              badgeClass = 'admission-badge';
              badgeText = 'Admission';
              break;
            case 'discharge':
              badgeClass = 'discharge-badge';
              badgeText = 'Discharge';
              break;
            case 'treatment':
              badgeClass = 'treatment-badge';
              badgeText = 'Treatment';
              break;
            case 'alert':
              badgeClass = 'alert-badge';
              badgeText = 'Alert';
              break;
            default:
              badgeClass = 'info-badge';
              badgeText = act.type.charAt(0).toUpperCase() + act.type.slice(1);
          }

          const content = act.description ? `<p class="feed-text">${act.description}</p>` : '<p class="feed-text">No details</p>';

          item.innerHTML = `
            <div class="feed-time">${act.time}</div>
            <div class="feed-content">
              <div class="feed-badge ${badgeClass}">${badgeText}</div>
              ${content}
            </div>
          `;
          feedList.appendChild(item);
        });
      }

      const wardsRes = await fetch('/api/live/wards');
      const wards = await wardsRes.json();
      wardList.innerHTML = '';
      wards.forEach(ward => {
        const percent = ward.percent;
        let meterClass = 'ok-meter';
        let textClass = 'ok-text';
        if (percent >= 90) {
          meterClass = 'critical-meter';
          textClass = 'critical-text';
        } else if (percent >= 80) {
          meterClass = 'warning-meter';
          textClass = 'warning-text';
        }

        const wardItem = document.createElement('div');
        wardItem.className = 'ward-item';
        wardItem.innerHTML = `
          <div class="ward-info">
            <h3>${ward.code || ward.name}</h3>
            <p>${ward.occupied} / ${ward.capacity} beds</p>
          </div>
          <div class="ward-meter ${meterClass}">
            <div class="meter-fill" style="width: ${percent}%;"></div>
          </div>
          <span class="ward-percent ${textClass}">${percent}%</span>
        `;
        wardList.appendChild(wardItem);
      });

      const now = new Date();
      lastUpdate.textContent = getUKTimeString(now);
    } catch (err) {
      // Silently handle fetch errors
    }
  }

  refreshLiveData();

  if (refreshBtn) {
    refreshBtn.addEventListener('click', refreshLiveData);
  }

  setInterval(refreshLiveData, 30000);
});