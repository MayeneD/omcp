/**
 * Modal module — open/close alert detail modal
 */
export function openAlertModal() {
  document.getElementById('alertModal').classList.add('open');
}

export function closeModal() {
  document.getElementById('alertModal').classList.remove('open');
}

export function initModal() {
  document.getElementById('alertModal').addEventListener('click', function (e) {
    if (e.target === this) closeModal();
  });
}
