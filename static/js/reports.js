document.addEventListener('DOMContentLoaded', () => {
  console.log('Reports.js loaded - page specific functionality only');
  
  const reportPeriod = document.getElementById('reportPeriod');

  // data for different periods
  const periodData = {
    today: {
      admissions: { value: '42', change: '+5% vs yesterday', trend: 'positive' },
      discharges: { value: '38', change: '+2% vs yesterday', trend: 'positive' },
      avgStay: { value: '4.2 days', change: 'No change', trend: 'neutral' },
      occupancy: { value: '82%', change: '+2% vs yesterday', trend: 'negative' },
      wardOccupancy: {
        AMU: 91,
        CCU: 86,
        ICU: 90,
        RESP: 73,
        SSS: 71,
        PAED: 70
      }
    },
    week: {
      admissions: { value: '324', change: '+12% vs last week', trend: 'positive' },
      discharges: { value: '298', change: '+8% vs last week', trend: 'positive' },
      avgStay: { value: '4.2 days', change: 'No change', trend: 'neutral' },
      occupancy: { value: '82%', change: '+5% vs last week', trend: 'negative' },
      wardOccupancy: {
        AMU: 91,
        CCU: 86,
        ICU: 90,
        RESP: 73,
        SSS: 71,
        PAED: 70
      }
    },
    month: {
      admissions: { value: '1,428', change: '+18% vs last month', trend: 'positive' },
      discharges: { value: '1,356', change: '+14% vs last month', trend: 'positive' },
      avgStay: { value: '4.5 days', change: '+0.3 days', trend: 'negative' },
      occupancy: { value: '85%', change: '+7% vs last month', trend: 'negative' },
      wardOccupancy: {
        AMU: 93,
        CCU: 89,
        ICU: 92,
        RESP: 78,
        SSS: 75,
        PAED: 73
      }
    },
    year: {
      admissions: { value: '18,642', change: '+22% vs last year', trend: 'positive' },
      discharges: { value: '17,894', change: '+19% vs last year', trend: 'positive' },
      avgStay: { value: '4.8 days', change: '+0.6 days', trend: 'negative' },
      occupancy: { value: '88%', change: '+10% vs last year', trend: 'negative' },
      wardOccupancy: {
        AMU: 95,
        CCU: 92,
        ICU: 94,
        RESP: 82,
        SSS: 79,
        PAED: 76
      }
    }
  };

  // update metrics cards
  function updateMetrics(period) {
    const data = periodData[period];

    // update metric values
    const metricCards = document.querySelectorAll('.metric-card');
    if (metricCards[0]) {
      metricCards[0].querySelector('.metric-value').textContent = data.admissions.value;
      const change1 = metricCards[0].querySelector('.metric-change');
      change1.textContent = data.admissions.change;
      change1.className = 'metric-change ' + data.admissions.trend;
    }

    if (metricCards[1]) {
      metricCards[1].querySelector('.metric-value').textContent = data.discharges.value;
      const change2 = metricCards[1].querySelector('.metric-change');
      change2.textContent = data.discharges.change;
      change2.className = 'metric-change ' + data.discharges.trend;
    }

    if (metricCards[2]) {
      metricCards[2].querySelector('.metric-value').textContent = data.avgStay.value;
      const change3 = metricCards[2].querySelector('.metric-change');
      change3.textContent = data.avgStay.change;
      change3.className = 'metric-change ' + data.avgStay.trend;
    }

    if (metricCards[3]) {
      metricCards[3].querySelector('.metric-value').textContent = data.occupancy.value;
      const change4 = metricCards[3].querySelector('.metric-change');
      change4.textContent = data.occupancy.change;
      change4.className = 'metric-change ' + data.occupancy.trend;
    }

    // update ward occupancy bars
    updateWardOccupancy(data.wardOccupancy);
  }

  // update ward occupancy chart
  function updateWardOccupancy(occupancy) {
    const barItems = document.querySelectorAll('.bar-item');
    
    barItems.forEach(item => {
      const label = item.querySelector('.bar-label').textContent;
      const fill = item.querySelector('.bar-fill');
      const value = item.querySelector('.bar-value');
      
      if (occupancy[label]) {
        const percent = occupancy[label];
        fill.style.width = percent + '%';
        value.textContent = percent + '%';
        
        // update color based on value
        fill.className = 'bar-fill';
        if (percent >= 90) {
          fill.classList.add('critical');
        } else if (percent >= 85) {
          fill.classList.add('warning');
        } else {
          fill.classList.add('ok');
        }
      }
    });
  }

  // period change handler
  if (reportPeriod) {
    reportPeriod.addEventListener('change', () => {
      const period = reportPeriod.value;
      updateMetrics(period);
      console.log('Report period changed to:', period);
    });

    // Initial load - set default period
    updateMetrics(reportPeriod.value);
  }
});