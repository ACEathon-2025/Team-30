import React, { useState } from 'react';

type SignalTiming = {
  green: number;
  yellow: number;
  red: number;
};

type Timings = {
  'north-south': SignalTiming;
  'east-west': SignalTiming;
};

const TrafficSliderInput: React.FC = () => {
  const [nsVehicles, setNsVehicles] = useState<number>(10);
  const [ewVehicles, setEwVehicles] = useState<number>(10);
  const [timings, setTimings] = useState<Timings | null>(null);
  const [error, setError] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setTimings(null);

    try {
      const response = await fetch('http://localhost:5001/api/signal-timings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ns_vehicles: nsVehicles,
          ew_vehicles: ewVehicles,
        }),
      });

      if (!response.ok) throw new Error('Failed to get timings');

      const data: Timings = await response.json();
      console.log(data)
      setTimings(data);
    } catch (err) {
      setError((err as Error).message || 'Something went wrong');
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          North-South Vehicles: {nsVehicles}
          <input
            type="range"
            min="0"
            max="100"
            value={nsVehicles}
            onChange={(e) => setNsVehicles(Number(e.target.value))}
          />
        </label>
        <br />
        <label>
          East-West Vehicles: {ewVehicles}
          <input
            type="range"
            min="0"
            max="100"
            value={ewVehicles}
            onChange={(e) => setEwVehicles(Number(e.target.value))}
          />
        </label>
        <br />
        <button type="submit">Get Signal Timings</button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {timings && (
        <div>
          <h3>Signal Timings</h3>
          <p>
            North-South: Green - {timings['north-south'].green}s, Yellow - {timings['north-south'].yellow}s, Red - {timings['north-south'].red}s
          </p>
          <p>
            East-West: Green - {timings['east-west'].green}s, Yellow - {timings['east-west'].yellow}s, Red - {timings['east-west'].red}s
          </p>
        </div>
      )}
    </div>
  );
};

export default TrafficSliderInput;
