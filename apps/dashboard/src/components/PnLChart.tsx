'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useStreamingData } from '../hooks/useStreamingData';

export default function PnLChart() {
  // Connect to Backend WebSocket (which streams ticks for now, in future PnL)
  const data = useStreamingData('ws://localhost:8000/');

  return (
    <div className="h-64 w-full bg-gray-900 rounded-lg p-4">
      <h3 className="text-white mb-4 font-semibold">Real-time Price Feed (Simulated PnL)</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="timestamp" tick={false} stroke="#9CA3AF" />
          <YAxis domain={['auto', 'auto']} stroke="#9CA3AF" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
            itemStyle={{ color: '#F3F4F6' }}
          />
          <Line type="monotone" dataKey="price" stroke="#8884d8" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
