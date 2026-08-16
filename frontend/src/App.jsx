import { useState, useEffect, useRef } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "./firebase";
import Login from "./Login";
import { listVideos, uploadVideo, connectStream } from "./api";

const API_BASE = "http://localhost:8000";
const PHASE_STYLES = {
  NORMAL: { bg: "bg-green-500/10", text: "text-green-400", ring: "ring-green-500/40", dot: "bg-green-400" },
  RISING: { bg: "bg-orange-500/10", text: "text-orange-400", ring: "ring-orange-500/50", dot: "bg-orange-400" },
  IMMINENT: { bg: "bg-red-500/10", text: "text-red-400", ring: "ring-red-500/60 animate-pulse", dot: "bg-red-400" },
};

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [activeView, setActiveView] = useState("monitor");
  const [videos, setVideos] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [logs, setLogs] = useState([]);
  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isEnded, setIsEnded] = useState(false);
  const [alertSettings, setAlertSettings] = useState({ email_enabled: true, sms_enabled: false });

  useEffect(() => onAuthStateChanged(auth, (u) => { setUser(u); setCheckingAuth(false); }), []);
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
      ctx.strokeStyle = "#4ade80";
      ctx.lineWidth = 2;
      ctx.font = "13px sans-serif";
      ctx.fillStyle = "#4ade80";
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
    setVideos((await listVideos()).videos);
  };

  const startStream = () => {
    if (!selected) return;
    if (wsRef.current) wsRef.current.close();
    setIsEnded(false); setIsStreaming(true); setLogs([]);
    wsRef.current = connectStream({ source_type: "file", filename: selected }, (payload) => {
      if (payload.type === "log") setLogs((prev) => [...prev.slice(-49), payload]);
      else setData(payload);
    });
    wsRef.current.onclose = () => { setIsStreaming(false); setIsEnded(true); };
  };
  const stopStream = () => { if (wsRef.current) wsRef.current.close(); setIsStreaming(false); };

  const toggleAlert = async (key) => {
    const updated = { ...alertSettings, [key]: !alertSettings[key] };
    setAlertSettings(updated);
    await fetch(`${API_BASE}/settings/alerts`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [key]: updated[key] }),
    });
  };

  const phase = data?.risk?.phase || "NORMAL";
  const ps = PHASE_STYLES[phase];

  if (checkingAuth) return <div className="min-h-screen bg-neutral-950" />;
  if (!user) return <Login onLogin={() => { }} />;

  const NAV_ITEMS = [
    { id: "monitor", label: "Monitor", icon: "◎" },
    { id: "reports", label: "Reports", icon: "▤" },
    { id: "settings", label: "Settings", icon: "⚙" },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex">
      <div className="w-52 bg-neutral-900/60 border-r border-neutral-800 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-8 px-1">
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-sm font-bold">S</div>
          <h1 className="text-base font-semibold tracking-tight">StampedeShield</h1>
        </div>
        <nav className="space-y-1 flex-1">
          {NAV_ITEMS.map((item) => (
            <button key={item.id} onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center gap-2.5 text-left px-3 py-2 rounded-lg text-sm font-medium transition ${activeView === item.id ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-neutral-400 hover:bg-neutral-800/70 hover:text-white"
                }`}>
              <span className="text-base opacity-80">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <button onClick={() => signOut(auth)} className="text-xs text-neutral-500 hover:text-neutral-300 text-left px-3">
          Log out
        </button>
      </div>

      <div className="flex-1 p-6 max-w-[1600px]">
        {activeView === "monitor" && (
          <div className="grid grid-cols-[1fr_320px] gap-5">
            <div className="space-y-4">
              {/* Hero risk banner */}
              <div className={`rounded-xl border border-neutral-800 ${ps.bg} px-5 py-4 flex items-center justify-between ring-1 ${ps.ring}`}>
                <div className="flex items-center gap-3">
                  <span className={`w-2.5 h-2.5 rounded-full ${ps.dot}`} />
                  <div>
                    <p className={`text-lg font-bold ${ps.text}`}>{phase}</p>
                    <p className="text-xs text-neutral-500">Live risk assessment</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-3xl font-bold tabular-nums ${ps.text}`}>{data?.risk?.score ?? "—"}</p>
                  <p className="text-xs text-neutral-500">risk score</p>
                </div>
              </div>

              <div className={`rounded-xl overflow-hidden border ${phase === "IMMINENT" ? "border-red-500/50" : phase === "RISING" ? "border-orange-500/40" : "border-neutral-800"} bg-black`}>
                <canvas ref={canvasRef} width={640} height={480} className="w-full h-auto block" />
              </div>

              <div className="grid grid-cols-4 gap-3">
                {[["People", data?.num_people ?? "—"], ["Density", data?.risk?.density ?? "—"], ["Entropy", data?.risk?.entropy ?? "—"], ["Stagnation", data?.risk?.stagnation ?? "—"]].map(([label, val]) => (
                  <div key={label} className="bg-neutral-900/60 border border-neutral-800 rounded-lg px-4 py-3">
                    <p className="text-xs text-neutral-500 mb-1">{label}</p>
                    <p className="text-lg font-semibold tabular-nums">{val}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 space-y-3">
                <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">Source</p>
                <label className="text-xs text-neutral-500 block mb-1">Upload video</label>
                <input type="file" accept="video/*" onChange={handleUpload}
                  className="text-xs w-full text-neutral-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-neutral-800 file:text-white file:text-xs" />
                <label className="text-xs text-neutral-500 block pt-1">Select video</label>
                <select value={selected} onChange={(e) => setSelected(e.target.value)}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-md px-3 py-2 text-sm">
                  <option value="">Select video</option>
                  {videos.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
                {videos.length === 0 && <p className="text-xs text-neutral-600">No videos uploaded yet</p>}
                {!isStreaming ? (
                  <button onClick={startStream} className="w-full bg-blue-600 hover:bg-blue-500 rounded-md py-2 text-sm font-semibold transition shadow-lg shadow-blue-600/20">Start Monitoring</button>
                ) : (
                  <button onClick={stopStream} className="w-full bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 rounded-md py-2 text-sm font-medium transition">Stop</button>
                )}
                {isEnded && <p className="text-xs text-neutral-600 text-center">Stream ended</p>}
              </div>

              <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-3">Event Log</p>
                <div className="h-56 overflow-y-auto text-xs space-y-1.5 pr-1">
                  {logs.length === 0 && <p className="text-neutral-700">No events yet</p>}
                  {logs.map((log, i) => (
                    <div key={i} className={`leading-relaxed ${log.event === "alert" ? "text-red-400" : log.event === "error" ? "text-red-300" :
                        log.event === "phase_change" ? "text-orange-300" : "text-neutral-500"}`}>
                      <span className="text-neutral-600">[{log.timestamp}]</span> {log.message}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === "settings" && (
          <div className="max-w-md">
            <h2 className="text-xl font-bold mb-1">Alert Settings</h2>
            <p className="text-sm text-neutral-500 mb-4">Control which channels fire on IMMINENT risk events.</p>
            <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 space-y-5">
              {[["email_enabled", "Email alerts"], ["sms_enabled", "SMS alerts"]].map(([key, label]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm">{label}</span>
                  <button onClick={() => toggleAlert(key)}
                    className={`w-11 h-6 rounded-full transition ${alertSettings[key] ? "bg-blue-600" : "bg-neutral-700"}`}>
                    <div className={`w-4.5 h-4.5 bg-white rounded-full transition-transform ${alertSettings[key] ? "translate-x-5" : "translate-x-1"}`} style={{ width: 18, height: 18 }} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeView === "reports" && <ReportsPanel />}
      </div>
    </div>
  );
}

function ReportsPanel() {
  const [reports, setReports] = useState([]);
  useEffect(() => {
    fetch(`${API_BASE}/reports`).then(r => r.json()).then(res => {
      setReports(res.reports.map((r, i) => ({ ...r, _index: i })).reverse());
    });
  }, []);
  const downloadReport = (index) => window.open(`${API_BASE}/reports/${index}/pdf`, "_blank");

  return (
    <div>
      <h2 className="text-xl font-bold mb-1">Session Reports</h2>
      <p className="text-sm text-neutral-500 mb-4">Download a PDF summary of any completed monitoring session.</p>
      {reports.length === 0 && <p className="text-neutral-600 text-sm">No completed sessions yet</p>}
      <div className="space-y-3">
        {reports.map((r) => (
          <div key={r._index} className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-medium text-sm">{r.source}</p>
                <p className="text-xs text-neutral-500">{r.start_time} · {r.duration_seconds}s</p>
              </div>
              <button onClick={() => downloadReport(r._index)}
                className="bg-blue-600 hover:bg-blue-500 text-xs font-medium px-3 py-1.5 rounded-md transition">
                Download PDF
              </button>
            </div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div><p className="text-neutral-500">Max people</p><p className="font-semibold">{r.max_people}</p></div>
              <div><p className="text-neutral-500">Max score</p><p className="font-semibold">{r.max_risk_score}</p></div>
              <div><p className="text-neutral-500">Alerts</p><p className="font-semibold">{r.alert_events.length}</p></div>
              <div><p className="text-neutral-500">Frames</p><p className="font-semibold">{r.frame_count}</p></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;