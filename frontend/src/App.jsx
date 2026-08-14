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

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const [videos, setVideos] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isEnded, setIsEnded] = useState(false);

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
    wsRef.current = connectStream(
      { source_type: "file", filename: selected },
      (payload) => setData(payload)
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

  const phase = data?.risk?.phase;

  if (checkingAuth) {
    return <div className="min-h-screen bg-neutral-950" />;
  }

  if (!user) {
    return <Login onLogin={() => {}} />;
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">StampedeShield</h1>
        <button
          onClick={() => signOut(auth)}
          className="text-sm text-neutral-400 hover:text-white"
        >
          Log out
        </button>
      </div>

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

            {isEnded && (
              <p className="text-xs text-neutral-500 text-center">Stream ended</p>
            )}
          </div>

          {data && (
            <div className="bg-neutral-900 rounded-lg p-4 space-y-3">
              <div className={`${PHASE_STYLES[phase]} rounded-md px-3 py-2 font-bold text-center`}>
                {phase} — {data.risk?.score}
              </div>
              <div className="flex justify-between text-sm text-neutral-400">
                <span>People</span>
                <span className="text-white font-medium">{data.num_people}</span>
              </div>
              <div className="flex justify-between text-sm text-neutral-400">
                <span>Density</span>
                <span className="text-white font-medium">{data.risk?.density}</span>
              </div>
              <div className="flex justify-between text-sm text-neutral-400">
                <span>Entropy</span>
                <span className="text-white font-medium">{data.risk?.entropy}</span>
              </div>
              <div className="flex justify-between text-sm text-neutral-400">
                <span>Stagnation</span>
                <span className="text-white font-medium">{data.risk?.stagnation}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;