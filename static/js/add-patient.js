document.addEventListener('DOMContentLoaded', () => {
  const dobInput = document.getElementById('dob');
  const ageInput = document.getElementById('age');
  const sexSelect = document.getElementById('sex');
  const wardSelect = document.getElementById('ward');
  const submitBtn = document.getElementById('submitBtn');
  const successAlert = document.getElementById('successAlert');
  const wardGenderError = document.getElementById('wardGenderError');
  const wardGenderInfo = document.getElementById('wardGenderInfo');

  if (dobInput && ageInput) {
    dobInput.addEventListener('change', () => {
      const dob = new Date(dobInput.value);
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const monthDiff = today.getMonth() - dob.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
      }
      ageInput.value = age >= 0 ? age : '';
    });
  }

  const admissionDateInput = document.getElementById('admissionDate');
  if (admissionDateInput) {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    admissionDateInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  function validateWardGender() {
    const patientSex = sexSelect.value;
    const selectedWard = wardSelect.options[wardSelect.selectedIndex];
    const wardGender = selectedWard ? selectedWard.getAttribute('data-gender') : null;

    wardGenderError.classList.remove('show');
    wardGenderInfo.classList.remove('show');
    wardSelect.classList.remove('invalid', 'valid');

    if (!patientSex) {
      if (wardSelect.value) wardGenderInfo.classList.add('show');
      return false;
    }
    if (!wardSelect.value) return true;
    if (wardGender === 'Mixed') {
      wardSelect.classList.add('valid');
      return true;
    }
    if (patientSex === 'Other') {
      wardGenderError.textContent = `⚠️ This ward only accepts ${wardGender} patients. Please select a Mixed ward for patients with "Other" sex.`;
      wardGenderError.classList.add('show');
      wardSelect.classList.add('invalid');
      return false;
    }
    if (wardGender !== patientSex) {
      const wardName = selectedWard.text.split(' - ')[0];
      wardGenderError.textContent = `⚠️ Gender mismatch! ${wardName} is for ${wardGender} patients only. Patient sex is ${patientSex}.`;
      wardGenderError.classList.add('show');
      wardSelect.classList.add('invalid');
      return false;
    }
    wardSelect.classList.add('valid');
    return true;
  }

  if (sexSelect) sexSelect.addEventListener('change', validateWardGender);
  if (wardSelect) wardSelect.addEventListener('change', validateWardGender);

  if (submitBtn) {
    submitBtn.addEventListener('click', (e) => {
      e.preventDefault();

      const firstName = document.getElementById('firstName').value.trim();
      const lastName = document.getElementById('lastName').value.trim();
      const dob = document.getElementById('dob').value;
      const sex = document.getElementById('sex').value;
      const nhsNumber = document.getElementById('nhsNumber').value.trim();
      const admissionDate = document.getElementById('admissionDate').value;
      const ward = document.getElementById('ward').value;
      const bed = document.getElementById('bed').value.trim();
      const consultant = document.getElementById('consultant').value;
      const diagnosis = document.getElementById('diagnosis').value.trim();

      if (!firstName) { alert('⚠️ Please enter patient first name'); document.getElementById('firstName').focus(); return; }
      if (!lastName) { alert('⚠️ Please enter patient last name'); document.getElementById('lastName').focus(); return; }
      if (!dob) { alert('⚠️ Please enter date of birth'); document.getElementById('dob').focus(); return; }
      if (!sex) { alert('⚠️ Please select patient sex'); document.getElementById('sex').focus(); return; }
      if (!nhsNumber) { alert('⚠️ Please enter NHS number'); document.getElementById('nhsNumber').focus(); return; }
      if (!admissionDate) { alert('⚠️ Please enter admission date and time'); document.getElementById('admissionDate').focus(); return; }
      if (!ward) { alert('⚠️ Please select a ward'); document.getElementById('ward').focus(); return; }
      if (!bed) { alert('⚠️ Please enter bed location'); document.getElementById('bed').focus(); return; }
      if (!consultant) { alert('⚠️ Please select a consultant'); document.getElementById('consultant').focus(); return; }
      if (!diagnosis) { alert('⚠️ Please enter primary diagnosis'); document.getElementById('diagnosis').focus(); return; }

      if (!validateWardGender()) {
        alert('❌ Cannot admit patient!\n\nWard gender type does not match patient sex.\n\nPlease select a compatible ward:\n• Male patients → Male or Mixed wards\n• Female patients → Female or Mixed wards\n• Other → Mixed wards only');
        document.getElementById('ward').focus();
        return;
      }

      const phone = document.getElementById('phone').value.trim();
      const address = document.getElementById('address').value.trim();
      const notes = document.getElementById('notes').value.trim();
      const age = document.getElementById('age').value;

      const patientData = { firstName, lastName, dob, age, sex, nhsNumber, phone, address, admissionDate, ward, bed, consultant, diagnosis, notes };

      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving...';

      fetch('/patients/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patientData)
      })
      .then(response => {
        if (!response.ok) return response.json().then(err => { throw new Error(err.error || 'Server error'); });
        return response.json();
      })
      .then(data => {
        if (successAlert) successAlert.style.display = 'flex';
        setTimeout(() => window.location.href = '/patients', 1500);
      })
      .catch(error => {
        if (error.message.includes('full')) alert('❌ ' + error.message);
        else alert('❌ Failed to add patient: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add patient';
      });
    });
  }

  // NHS number formatting
  const nhsNumberInput = document.getElementById('nhsNumber');
  if (nhsNumberInput) {
    nhsNumberInput.addEventListener('input', (e) => {
      let value = e.target.value.replace(/\D/g, '').substring(0, 10);
      if (value.length > 6) value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6);
      else if (value.length > 3) value = value.substring(0, 3) + ' ' + value.substring(3);
      e.target.value = value;
    });
  }

  const phoneInput = document.getElementById('phone');
  if (phoneInput) {
    phoneInput.addEventListener('input', (e) => {
      let value = e.target.value.replace(/\D/g, '').substring(0, 11);
      if (value.length > 5) value = value.substring(0, 5) + ' ' + value.substring(5);
      e.target.value = value;
    });
  }

  if (!sexSelect.value && wardGenderInfo) wardGenderInfo.classList.add('show');
});