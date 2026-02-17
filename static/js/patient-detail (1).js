// patient-detail.js
document.addEventListener('DOMContentLoaded', () => {
  // Example patient data – you can replace with real data later
  const patient = {
    id: 'P001',
    name: 'John Doe',
    gender: 'Male',
    age: '45 years',
    dob: '15 Jan 1981',
    bloodGroup: 'O+',
    ward: 'Ward A - Male Ward',
    bed: 'A01',
    admissionDate: '10 Feb 2026',
    contactNumber: '+44 7123 456789',
    emergencyContact: 'Jane Doe (Wife)',
    status: 'Stable',
    treatments: [
      {
        date: '12 Feb 2026',
        doctor: 'Dr. Sarah Smith',
        specialty: 'Cardiology',
        diagnosis: 'Hypertension',
        treatment: 'Medication prescribed',
        notes: 'Follow-up in 2 weeks'
      },
      {
        date: '11 Feb 2026',
        doctor: 'Dr. Michael Brown',
        specialty: 'General Medicine',
        diagnosis: 'Initial Assessment',
        treatment: 'Blood tests ordered',
        notes: 'Referred to cardiology'
      },
      {
        date: '10 Feb 2026',
        doctor: 'Dr. Emily Johnson',
        specialty: 'Emergency Medicine',
        diagnosis: 'Chest Pain',
        treatment: 'Emergency care',
        notes: 'Admitted to ward'
      }
    ],
    doctors: [
      {
        name: 'Dr. Sarah Smith',
        specialty: 'Cardiology',
        contact: 'Ext: 1234',
        email: 'sarah.smith@hospital.com',
        emoji: '👨⚕️'
      },
      {
        name: 'Dr. Michael Brown',
        specialty: 'General Medicine',
        contact: 'Ext: 5678',
        email: 'michael.brown@hospital.com',
        emoji: '👨⚕️'
      },
      {
        name: 'Dr. Emily Johnson',
        specialty: 'Emergency Medicine',
        contact: 'Ext: 9999',
        email: 'emily.johnson@hospital.com',
        emoji: '👩⚕️'
      }
    ]
  };

  // Helper to set text if element exists
  const setText = (selector, value) => {
    const el = document.querySelector(selector);
    if (el) el.textContent = value;
  };

  // Fill patient info section
  setText('[data-field="patient-id"]', patient.id);
  setText('[data-field="patient-name"]', patient.name);
  setText('[data-field="patient-gender"]', patient.gender);
  setText('[data-field="patient-age"]', patient.age);
  setText('[data-field="patient-dob"]', patient.dob);
  setText('[data-field="patient-blood"]', patient.bloodGroup);
  setText('[data-field="patient-ward"]', patient.ward);
  setText('[data-field="patient-bed"]', patient.bed);
  setText('[data-field="patient-admission"]', patient.admissionDate);
  setText('[data-field="patient-contact"]', patient.contactNumber);
  setText('[data-field="patient-emergency"]', patient.emergencyContact);
  setText('[data-field="patient-status"]', patient.status);

  // Status badge text if you have one
  const statusBadge = document.querySelector('.status-badge');
  if (statusBadge) statusBadge.textContent = patient.status;

  // Render treatment table
  const treatmentsBody = document.querySelector('[data-table="treatments-body"]');
  if (treatmentsBody) {
    treatmentsBody.innerHTML = '';
    patient.treatments.forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${t.date}</td>
        <td>${t.doctor}</td>
        <td>${t.specialty}</td>
        <td>${t.diagnosis}</td>
        <td>${t.treatment}</td>
        <td>${t.notes}</td>
      `;
      treatmentsBody.appendChild(tr);
    });
  }

  // Render treating doctors cards (if you want this dynamic)
  const doctorsGrid = document.querySelector('.doctors-grid[data-section="treating-doctors"]');
  if (doctorsGrid) {
    doctorsGrid.innerHTML = '';
    patient.doctors.forEach(d => {
      const card = document.createElement('div');
      card.className = 'doctor-card';
      card.innerHTML = `
        <div class="doctor-avatar">${d.emoji}</div>
        <div class="doctor-info">
          <h4>${d.name}</h4>
          <p class="doctor-specialty">${d.specialty}</p>
          <p class="doctor-contact">${d.contact}</p>
          <p class="doctor-email">${d.email}</p>
        </div>
      `;
      doctorsGrid.appendChild(card);
    });
  }

  // Back button
  const backBtn = document.querySelector('.back-btn');
  if (backBtn) {
    backBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = 'patient.html';
    });
  }

  // Print button
  const printBtn = document.querySelector('[data-action="print-detail"]');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  // Optional: theme/settings dropdown toggle if you have it in this page
  const settingsBtn = document.querySelector('.settings-btn');
  const settingsMenu = document.querySelector('.settings-menu');
  if (settingsBtn && settingsMenu) {
    settingsBtn.addEventListener('click', () => {
      settingsMenu.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!settingsBtn.contains(e.target) && !settingsMenu.contains(e.target)) {
        settingsMenu.classList.remove('open');
      }
    });
  }
});
