import React, { useState, useEffect } from 'react';

type SignalTiming = {
  green: number;
  yellow: number;
  red: number;
};

type Timings = {
  'north-south': SignalTiming;
  'east-west': SignalTiming;
};

type LiveResponse = Timings & {
  input: {
    ns_vehicles: number;
    ew_vehicles: number;
  };
};

const TrafficLiveDisplay: React.FC = () => {
  const [liveCounts, setLiveCounts] = useState({ ns_vehicles: 0, ew_vehicles: 0 });
  const [timings, setTimings] = useState<Timings | null>(null);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  const API_URL = 'http://localhost:5001/api/latest-timings';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(API_URL);
        if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
        const data: LiveResponse = await res.json();
        setLiveCounts(data.input);
        setTimings({ 'north-south': data['north-south'], 'east-west': data['east-west'] });
        setError('');
      } catch (err) {
        setError((err as Error).message || 'Failed to fetch data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); // fetch every 3s

    return () => clearInterval(interval);
  }, []);

  if (isLoading) return <div className="p-8 text-center">Connecting to Traffic System...</div>;
  if (error) return <div className="p-4 bg-red-100 text-red-700 rounded">{error}</div>;
  if (!timings) return null;

  return (
    <div className="max-w-xl mx-auto p-6 bg-gray-50 rounded shadow">
      <h2 className="text-2xl font-bold mb-6 text-center">Live Vehicle Counts & Signal Timings</h2>

      <div className="mb-6 bg-white p-4 rounded shadow">
        <h3 className="text-xl font-semibold mb-2">Vehicle Counts</h3>
        <p>North-South: <strong>{liveCounts.ns_vehicles}</strong></p>
        <p>East-West: <strong>{liveCounts.ew_vehicles}</strong></p>
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h3 className="text-xl font-semibold mb-3">Signal Timings (seconds)</h3>

        <div className="mb-4">
          <h4 className="font-semibold">North-South</h4>
          <p>Green: <span className="text-green-600 font-bold">{timings['north-south'].green}</span></p>
          <p>Yellow: <span className="text-yellow-500 font-bold">{timings['north-south'].yellow}</span></p>
          <p>Red: <span className="text-red-600 font-bold">{timings['north-south'].red}</span></p>
        </div>

        <div>
          <h4 className="font-semibold">East-West</h4>
          <p>Green: <span className="text-green-600 font-bold">{timings['east-west'].green}</span></p>
          <p>Yellow: <span className="text-yellow-500 font-bold">{timings['east-west'].yellow}</span></p>
          <p>Red: <span className="text-red-600 font-bold">{timings['east-west'].red}</span></p>
        </div>
      </div>
    </div>
  );
};

export default TrafficLiveDisplay;
