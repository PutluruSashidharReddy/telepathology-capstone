import React from 'react';

const BaselineTable = ({ baselines, drops }) => {
  if (!baselines) return null;

  return (
    <div className="mt-6 bg-[#1a1f2e] border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-2 border-b border-gray-700 pb-2">
        Protocol Benchmark Analysis <span className="text-xs text-red-400 ml-2">(Network Drops Simulated: {drops || 'Yes'})</span>
      </h3>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="text-xs text-gray-500 uppercase bg-[#111520]">
            <tr>
              <th className="px-4 py-2 rounded-tl-md">Protocol</th>
              <th className="px-4 py-2">Delivery Status</th>
              <th className="px-4 py-2">Data Overhead</th>
              <th className="px-4 py-2 rounded-tr-md">Efficiency</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-800">
              <td className="px-4 py-3 font-medium text-gray-300">TCP/IP</td>
              <td className="px-4 py-3">{baselines.TCP_IP?.status}</td>
              <td className="px-4 py-3">{baselines.TCP_IP?.overhead}</td>
              <td className="px-4 py-3 text-red-400">{baselines.TCP_IP?.efficiency}</td>
            </tr>
            <tr className="border-b border-gray-800">
              <td className="px-4 py-3 font-medium text-gray-300">Epidemic Routing</td>
              <td className="px-4 py-3">{baselines.Epidemic?.status}</td>
              <td className="px-4 py-3 text-yellow-500">{baselines.Epidemic?.overhead}</td>
              <td className="px-4 py-3">{baselines.Epidemic?.efficiency}</td>
            </tr>
            <tr className="border-b border-gray-800">
              <td className="px-4 py-3 font-medium text-gray-300">PRoPHET</td>
              <td className="px-4 py-3">{baselines.PRoPHET?.status}</td>
              <td className="px-4 py-3">{baselines.PRoPHET?.overhead}</td>
              <td className="px-4 py-3">{baselines.PRoPHET?.efficiency}</td>
            </tr>
            <tr className="bg-blue-900/20">
              <td className="px-4 py-3 font-bold text-blue-400">Neural DTN (Proposed)</td>
              <td className="px-4 py-3 font-bold text-blue-400">{baselines.Neural_DTN?.status}</td>
              <td className="px-4 py-3 font-bold text-blue-400">{baselines.Neural_DTN?.overhead}</td>
              <td className="px-4 py-3 font-bold text-green-400">{baselines.Neural_DTN?.efficiency}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BaselineTable;