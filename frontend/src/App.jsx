import { useState, useEffect, useRef } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "./firebase";
import Login from "./Login";
import { listVideos, uploadVideo, connectStream } from "./api";

const PHASE_STYLES = {
  NORMAL: "bg-green-500",
  RISING: "bg-orange-500",
  IMMINENT: "bg-red-500 animate-pulse",
};

const API_BASE = "http://localhost:8000";

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [activeView, setActiveView] = useState("monitor"); // monitor | reports | settings

  const [videos, setVideos] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [logs, setLogs] = useState([]);
  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isEnded, setIsEnded] = useState(false);

  const [alertSettings, setAlertSettings] = useState({ email_enabled: true, sms_enabled: false });

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setCheckingAuth(false);
    });
    return unsub;
  }, []);

  useEffect(() => {
    if (!user) return;
    listVideos().then((res) => setVideos(res.videos));
    fetch(`${API_BASE}/settings/alerts`).then(r => r.json()).then(setAlertSettings);
  }, [user]);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "#22c55e";
      ctx.lineWidth = 2;
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#22c55e";
      data.tracks.forEach((t) => {
        const [x1, y1, x2, y2] = t.bbox;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        ctx.fillText(`ID ${t.id}`, x1, y1 - 5);
      });
    };
    img.src = `data:image/jpeg;base64,${data.frame}`;
  }, [data]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await uploadVideo(file);
    const res = await listVideos();
    setVideos(res.videos);
  };

  const startStream = () => {
    if (!selected) return;
    if (wsRef.current) wsRef.current.close();
    setIsEnded(false);
    setIsStreaming(true);
    setLogs([]);
    wsRef.current = connectStream(
      { source_type: "file", filename: selected },
      (payload) => {
        if (payload.type === "log") {
          setLogs((prev) => [...prev.slice(-49), payload]);
        } else {
          setData(payload);
        }
      }
    );
    wsRef.current.onclose = () => {
      setIsStreaming(false);
      setIsEnded(true);
    };
  };

  const stopStream = () => {
    if (wsRef.current) wsRef.current.close();
    setIsStreaming(false);
  };

  const toggleAlert = async (key) => {
    const updated = { ...alertSettings, [key]: !alertSettings[key] };
    setAlertSettings(updated);
    await fetch(`${API_BASE}/settings/alerts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [key]: updated[key] }),
    });
  };

  const phase = data?.risk?.phase;

  if (checkingAuth) return <div className="min-h-screen bg-neutral-950" />;
  if (!user) return <Login onLogin={() => { }} />;

  const NAV_ITEMS = [
    { id: "monitor", label: "Monitor" },
    { id: "reports", label: "Reports" },
    { id: "settings", label: "Settings" },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex">
      {/* Left nav */}
      <div className="w-48 bg-neutral-900 border-r border-neutral-800 p-4 flex flex-col">
        <h1 className="text-lg font-bold mb-6">StampedeShield</h1>
        <nav className="space-y-1 flex-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition ${activeView === item.id
                  ? "bg-blue-600 text-white"
                  : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
                }`}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <button
          onClick={() => signOut(auth)}
          className="text-sm text-neutral-500 hover:text-white text-left"
        >
          Log out
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 p-6">
        {activeView === "monitor" && (
          <div className="flex gap-6">
            <div className="flex-1">
              <canvas
                ref={canvasRef}
                width={640}
                height={480}
                className="rounded-lg border border-neutral-800 bg-black w-full"
              />
            </div>

            <div className="w-72 space-y-4">
              <div className="bg-neutral-900 rounded-lg p-4 space-y-3">
                <label className="block text-sm text-neutral-400">Upload video</label>
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleUpload}
                  className="text-sm w-full file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-neutral-800 file:text-white text-neutral-400"
                />
                <label className="block text-sm text-neutral-400 pt-2">Select video</label>
                <select
                  value={selected}
                  onChange={(e) => setSelected(e.target.value)}
                  className="w-full bg-neutral-800 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select video</option>
                  {videos.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
                {videos.length === 0 && (
                  <p className="text-xs text-neutral-500">No videos uploaded yet</p>
                )}

                {!isStreaming ? (
                  <button
                    onClick={startStream}
                    className="w-full bg-blue-600 hover:bg-blue-500 rounded-md py-2 font-medium transition"
                  >
                    Start
                  </button>
                ) : (
                  <button
                    onClick={stopStream}
                    className="w-full bg-neutral-700 hover:bg-neutral-600 rounded-md py-2 font-medium transition"
                  >
                    Stop
                  </button>
                )}
                {isEnded && <p className="text-xs text-neutral-500 text-center">Stream ended</p>}
              </div>

              {data && (
                <div className="bg-neutral-900 rounded-lg p-4 space-y-3">
                  <div className={`${PHASE_STYLES[phase]} rounded-md px-3 py-2 font-bold text-center`}>
                    {phase} — {data.risk?.score}
                  </div>
                  <div className="flex justify-between text-sm text-neutral-400">
                    <span>People</span><span className="text-white font-medium">{data.num_people}</span>
                  </div>
                  <div className="flex justify-between text-sm text-neutral-400">
                    <span>Density</span><span className="text-white font-medium">{data.risk?.density}</span>
                  </div>
                  <div className="flex justify-between text-sm text-neutral-400">
                    <span>Entropy</span><span className="text-white font-medium">{data.risk?.entropy}</span>
                  </div>
                  <div className="flex justify-between text-sm text-neutral-400">
                    <span>Stagnation</span><span className="text-white font-medium">{data.risk?.stagnation}</span>
                  </div>
                </div>
              )}

              <div className="bg-neutral-900 rounded-lg p-4 h-48 overflow-y-auto text-xs space-y-1">
                <p className="text-neutral-400 font-medium mb-2">Event Log</p>
                {logs.length === 0 && <p className="text-neutral-600">No events yet</p>}
                {logs.map((log, i) => (
                  <div key={i} className={
                    log.event === "alert" ? "text-red-400" :
                      log.event === "error" ? "text-red-300" :
                        log.event === "phase_change" ? "text-orange-300" :
                          "text-neutral-400"
                  }>
                    [{log.timestamp}] {log.message}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeView === "settings" && (
          <div className="max-w-md">
            <h2 className="text-xl font-bold mb-4">Alert Settings</h2>
            <div className="bg-neutral-900 rounded-lg p-4 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Email alerts</span>
                <button
                  onClick={() => toggleAlert("email_enabled")}
                  className={`w-12 h-6 rounded-full transition ${alertSettings.email_enabled ? "bg-blue-600" : "bg-neutral-700"}`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition transform ${alertSettings.email_enabled ? "translate-x-6" : "translate-x-1"}`} />
                </button>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">SMS alerts</span>
                <button
                  onClick={() => toggleAlert("sms_enabled")}
                  className={`w-12 h-6 rounded-full transition ${alertSettings.sms_enabled ? "bg-blue-600" : "bg-neutral-700"}`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition transform ${alertSettings.sms_enabled ? "translate-x-6" : "translate-x-1"}`} />
                </button>
              </div>
            </div>
          </div>
        )}

        {activeView === "reports" && (
          <div>
            <h2 className="text-xl font-bold mb-4">Reports</h2>
            <p className="text-neutral-500 text-sm">Coming soon — session report generation.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;