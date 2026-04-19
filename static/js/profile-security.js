document.addEventListener('DOMContentLoaded', () => {

  // ── Reveal current password ───────────────────────────────────────────────
  const revealBtn        = document.getElementById('revealCurrentBtn');
  const currentPwInput   = document.getElementById('currentPassword');
  let passwordFetched    = false;

  if (revealBtn && currentPwInput) {
    revealBtn.addEventListener('click', async () => {
      if (passwordFetched) {
        const isHidden = currentPwInput.type === 'password';
        currentPwInput.type = isHidden ? 'text' : 'password';
        revealBtn.textContent = isHidden ? 'Hide' : 'Show';
        return;
      }

      revealBtn.disabled = true;
      revealBtn.textContent = '...';

      try {
        const response = await fetch('/api/get-password');
        const data = await response.json();

        if (data.success) {
          currentPwInput.value = data.password;
          currentPwInput.type = 'text';
          revealBtn.textContent = 'Hide';
          passwordFetched = true;
        } else {
          revealBtn.textContent = 'Show';
        }
      } catch {
        revealBtn.textContent = 'Show';
      }

      revealBtn.disabled = false;
    });
  }

  // ── Security form – change password via API ───────────────────────────────
  const securityForm  = document.getElementById('securityForm');
  const securityAlert = document.getElementById('securitySavedAlert');

  if (securityForm && securityAlert) {
    securityForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const currentPassword = currentPwInput ? currentPwInput.value : '';
      const newPassword     = document.getElementById('newPassword').value;
      const confirmPassword = document.getElementById('confirmPassword').value;

      if (!currentPassword || !newPassword || !confirmPassword) {
        showAlert(securityAlert, 'Please fill in all password fields.', true);
        return;
      }
      if (newPassword !== confirmPassword) {
        showAlert(securityAlert, 'New passwords do not match.', true);
        return;
      }
      if (newPassword.length < 8) {
        showAlert(securityAlert, 'New password must be at least 8 characters.', true);
        return;
      }

      const submitBtn = securityForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving...';

      try {
        const response = await fetch('/api/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ currentPassword, newPassword, confirmPassword }),
        });

        const data = await response.json();

        if (data.success) {
          showAlert(securityAlert, 'Password changed successfully.');
          securityForm.reset();
          passwordFetched = false;
          if (currentPwInput) currentPwInput.type = 'password';
          if (revealBtn) revealBtn.textContent = 'Show';
        } else {
          showAlert(securityAlert, data.error || 'Failed to change password.', true);
        }
      } catch {
        showAlert(securityAlert, 'Unable to reach the server. Please try again.', true);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Save security settings';
    });
  }

  function showAlert(el, message, isError = false) {
    const textSpan = el.querySelector('span:last-child');
    if (textSpan) textSpan.textContent = message;

    el.classList.toggle('inline-alert--error', isError);
    el.style.display = 'flex';
    setTimeout(() => {
      el.style.display = 'none';
      el.classList.remove('inline-alert--error');
    }, 3000);
  }
});