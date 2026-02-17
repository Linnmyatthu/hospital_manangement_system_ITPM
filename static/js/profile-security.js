document.addEventListener('DOMContentLoaded', () => {
  const profileForm = document.getElementById('profileForm');
  const profileAlert = document.getElementById('profileSavedAlert');
  const securityForm = document.getElementById('securityForm');
  const securityAlert = document.getElementById('securitySavedAlert');

  // fake save handlers
  if (profileForm && profileAlert) {
    profileForm.addEventListener('submit', (e) => {
      e.preventDefault();
      profileAlert.style.display = 'flex';
      setTimeout(() => { 
        profileAlert.style.display = 'none'; 
      }, 2500);
    });
  }

  if (securityForm && securityAlert) {
    securityForm.addEventListener('submit', (e) => {
      e.preventDefault();
      securityAlert.style.display = 'flex';
      setTimeout(() => { 
        securityAlert.style.display = 'none'; 
      }, 2500);
    });
  }
});