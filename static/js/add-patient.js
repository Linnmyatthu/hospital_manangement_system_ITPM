document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const dobInput = document.getElementById('dob');
  const ageInput = document.getElementById('age');
  const sexSelect = document.getElementById('sex');
  const wardSelect = document.getElementById('ward');
  const submitBtn = document.getElementById('submitBtn');
  const successAlert = document.getElementById('successAlert');
  const wardGenderError = document.getElementById('wardGenderError');
  const wardGenderInfo = document.getElementById('wardGenderInfo');

  /* MOBILE SIDEBAR TOGGLE */
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('sidebar-open');
      sidebar.classList.toggle('sidebar-closed');
    });

    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
        sidebar.classList.remove('sidebar-open');
        sidebar.classList.add('sidebar-closed');
      }
    });
  }

  /* AUTO-CALCULATE AGE FROM DOB */
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

  /* SET DEFAULT ADMISSION DATE TO NOW */
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

  /* WARD GENDER VALIDATION */
  function validateWardGender() {
    const patientSex = sexSelect.value;
    const selectedWard = wardSelect.options[wardSelect.selectedIndex];
    const wardGender = selectedWard ? selectedWard.getAttribute('data-gender') : null;

    // Hide all messages initially
    wardGenderError.classList.remove('show');
    wardGenderInfo.classList.remove('show');
    wardSelect.classList.remove('invalid', 'valid');

    // If no sex selected, show info message
    if (!patientSex) {
      if (wardSelect.value) {
        wardGenderInfo.classList.add('show');
      }
      return false;
    }

    // If no ward selected, don't validate yet
    if (!wardSelect.value) {
      return true;
    }

    // Check gender compatibility
    if (wardGender === 'Mixed') {
      wardSelect.classList.add('valid');
      return true;
    }

    // Convert sex value to full gender
    let patientGender;
    if (patientSex === 'M') {
      patientGender = 'Male';
    } else if (patientSex === 'F') {
      patientGender = 'Female';
    } else {
      // For "Other", only mixed wards are allowed
      if (wardGender !== 'Mixed') {
        wardGenderError.textContent = `⚠️ This ward only accepts ${wardGender} patients. Please select a Mixed ward for patients with "Other" sex.`;
        wardGenderError.classList.add('show');
        wardSelect.classList.add('invalid');
        return false;
      }
      wardSelect.classList.add('valid');
      return true;
    }

    // Validate gender match
    if (wardGender !== patientGender) {
      const wardName = selectedWard.text.split(' - ')[0];
      wardGenderError.textContent = `⚠️ Gender mismatch! ${wardName} is for ${wardGender} patients only. Patient sex is ${patientGender}.`;
      wardGenderError.classList.add('show');
      wardSelect.classList.add('invalid');
      return false;
    }

    wardSelect.classList.add('valid');
    return true;
  }

  // Validate when sex changes
  if (sexSelect) {
    sexSelect.addEventListener('change', () => {
      validateWardGender();
    });
  }

  // Validate when ward changes
  if (wardSelect) {
    wardSelect.addEventListener('change', () => {
      validateWardGender();
    });
  }

  /* FORM SUBMISSION */
  if (submitBtn) {
    submitBtn.addEventListener('click', (e) => {
      e.preventDefault();

      // Validate all required fields
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

      // Check required fields
      if (!firstName) {
        alert('⚠️ Please enter patient first name');
        document.getElementById('firstName').focus();
        return;
      }

      if (!lastName) {
        alert('⚠️ Please enter patient last name');
        document.getElementById('lastName').focus();
        return;
      }

      if (!dob) {
        alert('⚠️ Please enter date of birth');
        document.getElementById('dob').focus();
        return;
      }

      if (!sex) {
        alert('⚠️ Please select patient sex');
        document.getElementById('sex').focus();
        return;
      }

      if (!nhsNumber) {
        alert('⚠️ Please enter NHS number');
        document.getElementById('nhsNumber').focus();
        return;
      }

      if (!admissionDate) {
        alert('⚠️ Please enter admission date and time');
        document.getElementById('admissionDate').focus();
        return;
      }

      if (!ward) {
        alert('⚠️ Please select a ward');
        document.getElementById('ward').focus();
        return;
      }

      if (!bed) {
        alert('⚠️ Please enter bed location');
        document.getElementById('bed').focus();
        return;
      }

      if (!consultant) {
        alert('⚠️ Please select a consultant');
        document.getElementById('consultant').focus();
        return;
      }

      if (!diagnosis) {
        alert('⚠️ Please enter primary diagnosis');
        document.getElementById('diagnosis').focus();
        return;
      }

      // Validate ward gender compatibility
      if (!validateWardGender()) {
        alert('❌ Cannot admit patient!\n\nWard gender type does not match patient sex.\n\nPlease select a compatible ward:\n• Male patients → Male or Mixed wards\n• Female patients → Female or Mixed wards\n• Other → Mixed wards only');
        document.getElementById('ward').focus();
        return;
      }

      // Get optional fields
      const phone = document.getElementById('phone').value.trim();
      const address = document.getElementById('address').value.trim();
      const notes = document.getElementById('notes').value.trim();
      const age = document.getElementById('age').value;

      // Get ward and consultant names
      const wardName = wardSelect.options[wardSelect.selectedIndex].text;
      const consultantName = document.getElementById('consultant').options[document.getElementById('consultant').selectedIndex].text;

      // Create patient object
      const patientData = {
        firstName,
        lastName,
        fullName: `${firstName} ${lastName}`,
        dob,
        age,
        sex,
        nhsNumber,
        phone,
        address,
        admissionDate,
        ward,
        wardName,
        bed,
        consultant,
        consultantName,
        diagnosis,
        notes,
        timestamp: new Date().toISOString(),
        status: 'Active'
      };

      // In a real application, you would send this data to your backend
      // Example: fetch('/api/patients', { method: 'POST', body: JSON.stringify(patientData) })
      console.log('Patient data to be submitted:', patientData);

      // Show success message
      if (successAlert) {
        successAlert.style.display = 'flex';
      }
      
      // Simulate saving and redirect
      setTimeout(() => {
        const sexLabel = sex === 'M' ? 'Male' : sex === 'F' ? 'Female' : 'Other';
        
        alert(`✅ Patient Added Successfully!\n\n` +
              `Name: ${firstName} ${lastName}\n` +
              `Sex: ${sexLabel}\n` +
              `Age: ${age} years\n` +
              `NHS Number: ${nhsNumber}\n` +
              `Ward: ${wardName}\n` +
              `Bed: ${bed}\n` +
              `Consultant: ${consultantName}\n` +
              `Diagnosis: ${diagnosis}\n\n` +
              `Redirecting to patient list...`);
        
        window.location.href = 'patient.html';
      }, 1500);
    });
  }

  /* LIGHT/DARK MODE TOGGLE */
  const lightModeToggle = document.getElementById('lightModeToggle');
  if (lightModeToggle) {
    lightModeToggle.addEventListener('click', () => {
      // Check if theme.js provides the function
      if (typeof toggleThemeFromButton === 'function') {
        toggleThemeFromButton();
      } else {
        // Fallback if theme.js is not available
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        lightModeToggle.textContent = newTheme === 'light' ? 'Dark mode' : 'Light mode';
      }
    });
  }

  /* NHS NUMBER FORMATTING */
  const nhsNumberInput = document.getElementById('nhsNumber');
  if (nhsNumberInput) {
    nhsNumberInput.addEventListener('input', (e) => {
      // Remove all non-digits
      let value = e.target.value.replace(/\D/g, '');
      
      // Limit to 10 digits
      value = value.substring(0, 10);
      
      // Format as XXX XXX XXXX
      if (value.length > 6) {
        value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6);
      } else if (value.length > 3) {
        value = value.substring(0, 3) + ' ' + value.substring(3);
      }
      
      e.target.value = value;
    });
  }

  /* PHONE NUMBER FORMATTING */
  const phoneInput = document.getElementById('phone');
  if (phoneInput) {
    phoneInput.addEventListener('input', (e) => {
      // Remove all non-digits
      let value = e.target.value.replace(/\D/g, '');
      
      // Limit to 11 digits (UK phone)
      value = value.substring(0, 11);
      
      // Format as 07XXX XXXXXX
      if (value.length > 5) {
        value = value.substring(0, 5) + ' ' + value.substring(5);
      }
      
      e.target.value = value;
    });
  }

  /* SHOW INFO MESSAGE ON PAGE LOAD */
  if (!sexSelect.value && wardGenderInfo) {
    wardGenderInfo.classList.add('show');
  }

  console.log('Add Patient form initialized successfully');
});
