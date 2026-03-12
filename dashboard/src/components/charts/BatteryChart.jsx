import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function BatteryChart({ history }) {
  const windowMs = 120000; // 2 minutes
  const now = Date.now();
  const data = history
    .filter(h => now - h._localTime < windowMs)
    .map(h => ({
      time: ((h._localTime - now) / 1000).toFixed(0),
      battery: h.battery_pct,
    }));

  return (
    <div className="chart-container" data-testid="battery-chart">
      <h3>Battery (%)</h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} unit="%" />
          <Tooltip />
          <Line type="monotone" dataKey="battery" stroke="var(--chart-1)" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
