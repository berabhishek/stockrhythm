import PnLChart from '../components/PnLChart';
import StrategyTable from '../components/StrategyTable';
import LogViewer from '../components/LogViewer';
import { Activity, Terminal, ShieldAlert } from 'lucide-react';

export default function Home() {
  return (
    <main className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            StockRhythm
          </h1>
          <p className="text-gray-400">System Status: <span className="text-green-400">Operational</span></p>
        </div>
        <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md flex items-center gap-2 font-bold animate-pulse">
          <ShieldAlert size={20} />
          EMERGENCY KILL
        </button>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Chart Area */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
            <div className="flex items-center gap-2 mb-4 text-gray-300">
              <Activity size={20} />
              <h2 className="font-semibold">Performance Overview</h2>
            </div>
            <PnLChart />
          </div>

          <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
            <h2 className="font-semibold text-gray-300 mb-4">Active Strategies</h2>
            <StrategyTable />
          </div>
        </div>

        {/* Sidebar / Logs */}
        <div className="lg:col-span-1 space-y-6">
           <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-4 text-gray-300">
              <Terminal size={20} />
              <h2 className="font-semibold">System Logs</h2>
            </div>
            <div className="flex-1">
              <LogViewer />
            </div>
           </div>
        </div>

      </div>
    </main>
  )
}
