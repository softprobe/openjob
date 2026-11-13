/* Copy the permalink and draw a WeChat QR code. No network requests. */

document.addEventListener("click", (event) => {
  const emailButton = event.target.closest("[data-copy-email]");
  if (emailButton) {
    copyText(emailButton.getAttribute("data-copy-email") || "", emailButton);
    return;
  }
  const copy = event.target.closest("[data-copy]");
  if (copy) {
    const root = copy.closest("[data-permalink]");
    if (!root) return;
    copyPermalink(root, copy);
    return;
  }
  const wechat = event.target.closest("[data-wechat]");
  if (wechat) {
    const root = wechat.closest("[data-permalink]");
    if (!root) return;
    toggleWeChat(root, wechat);
  }
});

function copyPermalink(root, button) {
  const url = root.getAttribute("data-permalink") || "";
  const input = root.querySelector(".permalink");
  if (input) {
    input.focus();
    input.select();
  }
  const fallback = () => {
    try {
      document.execCommand("copy");
    } catch (error) {
      /* The permalink field stays selected when the clipboard is blocked. */
    }
  };
  copyText(url, button, fallback);
}

function copyText(text, button, fallback) {
  const done = () => {
    const label = button.getAttribute("data-done") || "Copied";
    const previous = button.textContent;
    button.textContent = label;
    window.setTimeout(() => {
      button.textContent = previous;
    }, 1600);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(() => {
      if (fallback) fallback();
      done();
    });
    return;
  }
  if (fallback) fallback();
  done();
}

function toggleWeChat(root, button) {
  const panel = root.querySelector(".qr-panel");
  if (!panel) return;
  const open = panel.hasAttribute("hidden");
  if (!open) {
    panel.setAttribute("hidden", "");
    button.setAttribute("aria-expanded", "false");
    return;
  }
  panel.removeAttribute("hidden");
  button.setAttribute("aria-expanded", "true");
  const canvas = panel.querySelector("canvas");
  if (!canvas || canvas.dataset.ready === "1") return;
  try {
    drawQr(canvas, root.getAttribute("data-permalink") || "");
    canvas.dataset.ready = "1";
  } catch (error) {
    const note = document.createElement("p");
    note.className = "sub";
    note.textContent = "Copy the link and paste it into WeChat.";
    panel.appendChild(note);
    canvas.dataset.ready = "1";
  }
}

function drawQr(canvas, text) {
  if (typeof qrcode !== "function") {
    throw new Error("QR library missing");
  }
  const qr = qrcode(0, "M");
  qr.addData(text);
  qr.make();
  const count = qr.getModuleCount();
  const scale = 4;
  const margin = 4;
  const size = (count + margin * 2) * scale;
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#f3efe4";
  ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = "#1c1915";
  for (let row = 0; row < count; row += 1) {
    for (let col = 0; col < count; col += 1) {
      if (qr.isDark(row, col)) {
        ctx.fillRect((col + margin) * scale, (row + margin) * scale, scale, scale);
      }
    }
  }
}
