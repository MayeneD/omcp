/**
 * Clock module — updates all UTC clock elements every second
 */
export function startClock() {
  function updateClock() {
    const t = new Date().toUTCString().slice(17, 25);
    document.querySelectorAll('[id^="clock"]').forEach(el => {
      el.textContent = t + ' UTC';
    });
  }
  setInterval(updateClock, 1000);
  updateClock();
}
