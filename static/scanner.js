const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const manualInput = document.getElementById("manualBarcode");
const lookupBtn = document.getElementById("lookupBtn");

function renderRecord(record) {
  resultEl.innerHTML = "";
  Object.entries(record).forEach(([key, value]) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `<strong>${key}</strong><br>${value}`;
    resultEl.appendChild(div);
  });
}

async function lookupBarcode(value) {
  if (!value) return;

  statusEl.textContent = "Searching...";
  try {
    const response = await fetch(`/api/lookup?value=${encodeURIComponent(value)}`);
    const payload = await response.json();

    if (!payload.found) {
      resultEl.innerHTML = "";
      statusEl.textContent = payload.message || "No record found.";
      return;
    }

    statusEl.textContent = "Record found.";
    renderRecord(payload.record);
  } catch (error) {
    statusEl.textContent = "Lookup failed. Please try again.";
  }
}

lookupBtn.addEventListener("click", () => {
  lookupBarcode(manualInput.value.trim());
});

if (window.Html5Qrcode) {
  const scanner = new Html5Qrcode("reader");
  Html5Qrcode.getCameras()
    .then((devices) => {
      if (!devices || !devices.length) {
        statusEl.textContent = "No camera found. Use manual lookup.";
        return;
      }

      scanner.start(
        devices[0].id,
        { fps: 10, qrbox: { width: 250, height: 90 } },
        (decodedText) => {
          manualInput.value = decodedText;
          lookupBarcode(decodedText);
          scanner.pause(true);
        }
      );
    })
    .catch(() => {
      statusEl.textContent = "Camera unavailable. Use manual lookup.";
    });
} else {
  statusEl.textContent = "Scanner library unavailable. Use manual lookup.";
}
