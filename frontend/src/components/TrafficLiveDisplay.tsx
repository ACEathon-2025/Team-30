import React, { useState, useEffect } from 'react';

// --- TYPE DEFINITIONS ---
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
    }
}

// --- Traffic Light Component ---
const TrafficLight = ({ color, isActive }: { color: 'red' | 'yellow' | 'green', isActive: boolean }) => (
    <div className={`w-10 h-10 rounded-full mb-2 border-2 border-gray-700 transition-all duration-300 ${
        isActive 
            ? color === 'red' ? 'bg-red-600 shadow-red-500/80 shadow-lg' : 
              color === 'yellow' ? 'bg-yellow-400 shadow-yellow-500/80 shadow-lg' : 
              'bg-green-500 shadow-green-500/80 shadow-lg'
            : 'bg-gray-800'
    }`} />
);

// --- Signal Column Component ---
const SignalColumn = ({ direction, timings, currentPhase }: { direction: string, timings: SignalTiming, currentPhase: 'red' | 'yellow' | 'green' }) => {
    const isGreen = currentPhase === 'green';
    const isYellow = currentPhase === 'yellow';
    const isRed = currentPhase === 'red';

    const currentDuration = isRed ? timings.red : isYellow ? timings.yellow : timings.green;

    return (
        <div className="bg-gray-100 p-6 rounded-xl shadow-2xl w-full max-w-sm flex flex-col items-center">
            <h4 className="text-xl font-extrabold mb-4 text-gray-800 border-b-2 border-gray-300 pb-2">{direction}</h4>
            <div className="flex flex-col items-center p-4 bg-gray-900 rounded-2xl shadow-inner mb-4">
                <TrafficLight color="red" isActive={isRed} />
                <TrafficLight color="yellow" isActive={isYellow} />
                <TrafficLight color="green" isActive={isGreen} />
            </div>
            <p className="text-lg font-semibold text-gray-700">
                Current Phase: <span className={`font-bold uppercase ${isGreen ? 'text-green-500' : isYellow ? 'text-yellow-500' : 'text-red-500'}`}>{currentPhase}</span>
            </p>
            <p className="text-sm text-gray-500">
                Time Remaining: <span className="font-mono text-base text-indigo-600">{currentDuration}s</span>
            </p>
        </div>
    );
}

// --- Traffic Live Display Component ---
const TrafficLiveDisplay: React.FC = () => {
    const [liveCounts, setLiveCounts] = useState<{ ns_vehicles: number, ew_vehicles: number }>({ ns_vehicles: 0, ew_vehicles: 0 });
    const [timings, setTimings] = useState<Timings | null>(null);
    const [error, setError] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(true);

    const [currentPhaseNS, setCurrentPhaseNS] = useState<'red' | 'yellow' | 'green'>('red');
    const [currentPhaseEW, setCurrentPhaseEW] = useState<'red' | 'yellow' | 'green'>('green');
    const [timeRemaining, setTimeRemaining] = useState<number>(0);

    const API_URL = 'http://localhost:5001/api/latest-timings';

    // --- Poll backend for latest timings ---
    useEffect(() => {
        const fetchTimings = async () => {
            try {
                const response = await fetch(API_URL); 
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data: LiveResponse = await response.json();
                setLiveCounts(data.input);
                setTimings({
                    'north-south': data['north-south'],
                    'east-west': data['east-west'],
                });
            } catch (err) {
                setError((err as Error).message || 'Failed to connect to backend.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchTimings();
        const intervalId = setInterval(fetchTimings, 5000);
        return () => clearInterval(intervalId);
    }, []);

    // --- Traffic Light Cycle Simulation ---
    useEffect(() => {
        if (!timings) return;

        const cycleDurations = {
            'NS_GREEN': timings['north-south'].green,
            'NS_YELLOW': timings['north-south'].yellow,
            'EW_GREEN': timings['east-west'].green,
            'EW_YELLOW': timings['east-west'].yellow,
        };

        if (timeRemaining <= 0) {
            if (currentPhaseEW === 'green') {
                setCurrentPhaseEW('green'); setCurrentPhaseNS('red'); setTimeRemaining(cycleDurations.EW_GREEN);
            } else {
                setCurrentPhaseNS('green'); setCurrentPhaseEW('red'); setTimeRemaining(cycleDurations.NS_GREEN);
            }
            return;
        }

        const timer = setTimeout(() => {
            if (timeRemaining > 1) setTimeRemaining(prev => prev - 1);
            else {
                if (currentPhaseNS === 'green') { setCurrentPhaseNS('yellow'); setTimeRemaining(cycleDurations.NS_YELLOW); }
                else if (currentPhaseNS === 'yellow') { setCurrentPhaseNS('red'); setCurrentPhaseEW('green'); setTimeRemaining(cycleDurations.EW_GREEN); }
                else if (currentPhaseEW === 'green') { setCurrentPhaseEW('yellow'); setTimeRemaining(cycleDurations.EW_YELLOW); }
                else if (currentPhaseEW === 'yellow') { setCurrentPhaseEW('red'); setCurrentPhaseNS('green'); setTimeRemaining(cycleDurations.NS_GREEN); }
            }
        }, 1000);

        return () => clearTimeout(timer);
    }, [timings, timeRemaining, currentPhaseNS, currentPhaseEW]);

    if (isLoading) return <div className="text-center p-8">Connecting to Live Traffic System...</div>;
    if (error) return <div className="text-red-700 p-4 bg-red-100 rounded-lg">ERROR: {error}</div>;
    if (!timings) return null;

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            {/* LIVE VEHICLE COUNTS */}
            <div className="max-w-4xl mx-auto mb-12 p-6 bg-white rounded-xl shadow-lg border-t-4 border-indigo-500">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">LIVE VEHICLE COUNTS (CV Input)</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-lg">
                    <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-gray-600">North/South Lanes Detected:</p>
                        <strong className="text-3xl font-extrabold text-indigo-700">{liveCounts.ns_vehicles}</strong>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-gray-600">East/West Lanes Detected:</p>
                        <strong className="text-3xl font-extrabold text-indigo-700">{liveCounts.ew_vehicles}</strong>
                    </div>
                </div>
            </div>

            {/* SIGNAL TIMINGS */}
            <div className="max-w-4xl mx-auto mb-12 p-6 bg-white rounded-xl shadow-lg border-t-4 border-green-500">
                <h2 className="text-2xl font-bold mb-6 text-gray-800">ML CALCULATED SIGNAL SCHEDULE</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                        <h4 className="text-xl font-bold text-gray-700 mb-2">North-South Optimal Times:</h4>
                        <ul className="space-y-1 text-gray-600">
                            <li className="flex justify-between">Green: <span className="text-green-600 font-semibold">{timings['north-south'].green}s</span></li>
                            <li className="flex justify-between">Yellow: <span className="text-yellow-500 font-semibold">{timings['north-south'].yellow}s</span></li>
                            <li className="flex justify-between">Red: <span className="text-red-600 font-semibold">{timings['north-south'].red}s</span></li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-xl font-bold text-gray-700 mb-2">East-West Optimal Times:</h4>
                        <ul className="space-y-1 text-gray-600">
                            <li className="flex justify-between">Green: <span className="text-green-600 font-semibold">{timings['east-west'].green}s</span></li>
                            <li className="flex justify-between">Yellow: <span className="text-yellow-500 font-semibold">{timings['east-west'].yellow}s</span></li>
                            <li className="flex justify-between">Red: <span className="text-red-600 font-semibold">{timings['east-west'].red}s</span></li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* LIVE SIGNAL SIMULATION */}
            <div className="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg border-t-4 border-purple-500">
                <h2 className="text-2xl font-bold mb-8 text-gray-800 text-center">LIVE SIGNAL SIMULATION</h2>
                <div className="flex flex-col md:flex-row justify-around gap-8">
                    <SignalColumn direction="North-South" timings={timings['north-south']} currentPhase={currentPhaseNS} />
                    <SignalColumn direction="East-West" timings={timings['east-west']} currentPhase={currentPhaseEW} />
                </div>
            </div>
        </div>
    );
};

export default TrafficLiveDisplay;
