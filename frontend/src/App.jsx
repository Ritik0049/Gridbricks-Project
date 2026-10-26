import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer,
} from "recharts";
import "./App.css";

const API =
  import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

const fmtTime = (t) =>
  new Date(t).toLocaleString("en-GB", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "UTC",
  });
const mw = (v) => (v == null ? "-" : `${v.toLocaleString()} MW`);

export default function App() {
  const [start, setStart] = useState("2026-01-02");
  const [end, setEnd] = useState("2026-01-08");
  const [horizon, setHorizon] = useState(4);
  const [data, setData] = useState(null);
  const [curve, setCurve] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const q = new URLSearchParams({ start, end, horizon });
    fetch(`${API}/api/series?${q}`)
      .then((r) => {
        if (!r.ok) throw new Error(`API error ${r.status}`);
        return r.json();
      })
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e.message));
  }, [start, end, horizon]);

  useEffect(() => {
    fetch(`${API}/api/horizon-curve?${new URLSearchParams({ start, end })}`)
      .then((r) => r.json())
      .then(setCurve)
      .catch(() => setCurve([]));
  }, [start, end]);

  const m = data?.metrics;

  return (
    <div className="wrap">
      <h1>UK Wind Forecast Monitor</h1>
      <p className="sub">
        National wind generation vs the forecast that was actually available at decision time. January 2026.
      </p>

      <div className="controls">
        <label>
          From
          <input type="date" value={start} min="2026-01-01" max={end}
            onChange={(e) => setStart(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={end} min={start} max="2026-02-01"
            onChange={(e) => setEnd(e.target.value)} />
        </label>
        <label className="slider">
          Forecast horizon: {horizon}h before delivery
          <input type="range" min="0" max="48" step="1" value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))} />
        </label>
      </div>

      {error && <p className="err">Could not load data: {error}</p>}

      {m && (
        <>
          <div className="cards">
            <div className="card"><div className="k">Mean absolute error</div><div className="v">{mw(m.mae)}</div></div>
            <div className="card"><div className="k">RMSE</div><div className="v">{mw(m.rmse)}</div></div>
            <div className="card"><div className="k">Bias (+ means over-forecast)</div><div className="v">{mw(m.bias)}</div></div>
            <div className="card"><div className="k">P90 absolute error</div><div className="v">{mw(m.p90_abs_error)}</div></div>
            <div className="card"><div className="k">MAE as % of output</div><div className="v">{m.mae_pct}%</div></div>
          </div>

          <div className="insight">
            Using forecasts made {horizon}h ahead, the forecast misses by <b>{mw(m.mae)}</b> on average,
            and 9 times out of 10 the miss is under <b>{mw(m.p90_abs_error)}</b>. That P90 figure is a
            sensible buffer to hold when deciding how much extra power to buy.
          </div>
        </>
      )}

      <div className="panel">
        <h2>Actual vs forecast generation</h2>
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={data?.points ?? []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tickFormatter={fmtTime} minTickGap={60} />
            <YAxis tickFormatter={(v) => `${v / 1000}k`} label={{ value: "MW", angle: -90, position: "insideLeft" }} />
            <Tooltip labelFormatter={fmtTime} formatter={(v) => mw(v)} />
            <Legend />
            <Line type="monotone" dataKey="actual" name="Actual" stroke="#2563eb" dot={false} />
            <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#16a34a" dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h2>How error grows with forecast horizon</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={curve}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="horizon" tickFormatter={(h) => `${h}h`} />
            <YAxis />
            <Tooltip labelFormatter={(h) => `${h}h ahead`} formatter={(v) => mw(v)} />
            <Legend />
            <Line dataKey="mae" name="Mean absolute error" stroke="#2563eb" />
            <Line dataKey="p90" name="P90 error" stroke="#dc2626" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}