import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MOTOR_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)'];

export default function MotorRPMChart({ history }) {
  const windowMs = 30000; // 30 seconds
  const now = Date.now();
  const data = history
    .filter(h => now - h._localTime < windowMs)
    .map(h => ({
      time: ((h._localTime - now) / 1000).toFixed(0),
      motor0: h.motor_rpm ? h.motor_rpm[0] : 0,
      motor1: h.motor_rpm ? h.motor_rpm[1] : 0,
      motor2: h.motor_rpm ? h.motor_rpm[2] : 0,
      motor3: h.motor_rpm ? h.motor_rpm[3] : 0,
    }));

  return (
    <div className="chart-container" data-testid="motor-rpm-chart">
      <h3>Motor RPM</h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 8000]} />
          <Tooltip />
          {[0, 1, 2, 3].map(i => (
            <Line key={i} type="monotone" dataKey={`motor${i}`} stroke={MOTOR_COLORS[i]} dot={false} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
