'use client';

import { Zap, PauseCircle, Trash2, Pencil } from 'lucide-react';

const STRATEGIES = [
  { id: 1, name: 'TrendFollower_BTC', regime: 'Active', pnl: '+12.5%' },
  { id: 2, name: 'MeanRev_AAPL', regime: 'Paused', pnl: '-2.1%' },
];

export default function StrategyTable() {
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <table className="w-full text-left text-sm text-gray-400">
        <thead className="bg-gray-800 text-gray-200 uppercase">
          <tr>
            <th className="px-6 py-3">Strategy Name</th>
            <th className="px-6 py-3">Regime</th>
            <th className="px-6 py-3">PnL</th>
            <th className="px-6 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {STRATEGIES.map((strategy) => (
            <tr key={strategy.id} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="px-6 py-4 font-medium text-white">{strategy.name}</td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-xs ${strategy.regime === 'Active' ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
                  {strategy.regime}
                </span>
              </td>
              <td className={`px-6 py-4 ${strategy.pnl.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                {strategy.pnl}
              </td>
              <td className="px-6 py-4 text-right flex justify-end gap-2">
                 <button className="p-1 hover:text-white" title="Run"><Zap size={16} /></button>
                 <button className="p-1 hover:text-white" title="Pause"><PauseCircle size={16} /></button>
                 <button className="p-1 hover:text-white" title="Edit"><Pencil size={16} /></button>
                 <button className="p-1 text-red-500 hover:text-red-400" title="Delete"><Trash2 size={16} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
