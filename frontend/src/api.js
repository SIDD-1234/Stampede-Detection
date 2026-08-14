const API_BASE = "http://localhost:8000";

export async function listVideos() {
  const res = await fetch(`${API_BASE}/videos`);
  return res.json();
}

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
  return res.json();
}

export function connectStream(sourceConfig, onMessage) {
  const ws = new WebSocket("ws://localhost:8000/ws/stream");
  ws.onopen = () => ws.send(JSON.stringify(sourceConfig));
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws;
}