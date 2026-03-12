import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function TemperatureChart({ history }) {
  const windowMs = 300000; // 5 minutes
  const now = Date.now();
  const data = history
    .filter(h => now - h._localTime < windowMs)
    .map(h => ({
      time: ((h._localTime - now) / 1000).toFixed(0),
      temp: h.internal_temp_c,
    }));

  return (
    <div className="chart-container" data-testid="temperature-chart">
      <h3>Temperature ({'\u00B0'}C)</h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[20, 70]} unit={'\u00B0C'} />
          <Tooltip />
          <Line type="monotone" dataKey="temp" stroke="var(--chart-2)" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
