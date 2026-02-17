document.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('saveNotificationSettings');
  const alertBox = document.getElementById('notificationSavedAlert');

  // fake save + inline confirmation
  if (saveBtn && alertBox) {
    saveBtn.addEventListener('click', () => {
      alertBox.style.display = 'flex';
      setTimeout(() => {
        alertBox.style.display = 'none';
      }, 2500);
    });
  }
});