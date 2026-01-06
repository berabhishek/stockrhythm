export default function LogViewer() {
  const logs = [
    "[10:00:01] INFO: System started",
    "[10:00:05] INFO: Connected to Upstox Provider",
    "[10:01:23] WARN: High latency detected (200ms)",
    "[10:02:00] TRADE: BUY AAPL @ 150.20",
  ];

  return (
    <div className="bg-black rounded-lg p-4 h-64 overflow-y-auto font-mono text-xs text-green-400 border border-gray-800">
      {logs.map((log, i) => (
        <div key={i} className="mb-1">{log}</div>
      ))}
    </div>
  );
}
