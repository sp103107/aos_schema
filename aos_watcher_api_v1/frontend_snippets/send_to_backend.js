// Minimal "Send to backend" button handler (FastAPI /submit_json)
// Add a button in HTML: <button id="send_backend_btn" ...>Send to backend</button>
document.getElementById("send_backend_btn").addEventListener("click", async () => {
  const out = document.getElementById("output_json").value;
  if (!out.trim()) { alert("Create envelope first"); return; }
  const env = JSON.parse(out);

  // If you also want to send agent profiles, wrap as bundle:
  // const bundle = { envelope: env, agent_profiles: JSON.parse(document.getElementById("agent_profiles_json").value) };

  const res = await fetch("http://localhost:8787/submit_json", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(env)
  });

  const data = await res.json();
  alert("Submitted: " + data.id);
});
