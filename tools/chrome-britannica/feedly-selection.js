// Keep Chrome's selection menu available before Feedly's page handlers run.
// Do not cancel the default action: that default action opens the native menu.
window.addEventListener("contextmenu", (event) => {
  if (window.getSelection()?.toString().trim()) {
    event.stopImmediatePropagation();
  }
}, {capture: true});
