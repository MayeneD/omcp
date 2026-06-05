import { startClock } from './clock.js';
import { goTo, markActiveNav } from './navigation.js';
import { initModal, openAlertModal, closeModal } from './modal.js';

document.addEventListener('DOMContentLoaded', () => {
  startClock();
  markActiveNav();
  const modal = document.getElementById('alertModal');
  if (modal) initModal();
  window.goTo = goTo;
  window.openAlertModal = openAlertModal;
  window.closeModal = closeModal;
});
