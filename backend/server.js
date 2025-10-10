const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 5001;

// --- Middleware ---
app.use(cors());
app.use(express.json());

// --- Global State ---
// Stores latest vehicle counts + optimized timings
let latestData = {
  input: {
    ns_vehicles: 0,
    ew_vehicles: 0
  },
  timings: {
    ns_time: 10,
    ew_time: 10
  }
};

// --- POST Endpoint (Python → Node.js) ---
// Expected payload: { ns_vehicles, ew_vehicles, ns_time, ew_time }
app.post('/api/update-counts', (req, res) => {
  const { ns_vehicles, ew_vehicles, ns_time, ew_time } = req.body;

  // Validation
  if (
    ns_time === undefined || ew_time === undefined ||
    ns_vehicles === undefined || ew_vehicles === undefined
  ) {
    return res.status(400).json({ error: 'Missing fields: ns_vehicles, ew_vehicles, ns_time, or ew_time.' });
  }

  // Update the latest global state
  latestData = {
    input: {
      ns_vehicles: parseInt(ns_vehicles, 10),
      ew_vehicles: parseInt(ew_vehicles, 10)
    },
    timings: {
      ns_time: parseInt(ns_time, 10),
      ew_time: parseInt(ew_time, 10)
    }
  };

  console.log(`[POST /api/update-counts] ✅ Updated data:
  NS Vehicles: ${latestData.input.ns_vehicles}, EW Vehicles: ${latestData.input.ew_vehicles}
  NS Time: ${latestData.timings.ns_time}s, EW Time: ${latestData.timings.ew_time}s`);

  res.status(200).json({ message: 'Data received successfully', data: latestData });
});

// --- GET Endpoint (Frontend → Node.js) ---
app.get('/api/latest-timings', (req, res) => {
  const YELLOW_TIME = 4; // Fixed yellow time
  const { ns_time, ew_time } = latestData.timings;

  // Compute red times based on opposing green + yellow
  const red_ns = ew_time + YELLOW_TIME;
  const red_ew = ns_time + YELLOW_TIME;

  const response = {
    input: latestData.input,
    'north-south': { green: ns_time, yellow: YELLOW_TIME, red: red_ns },
    'east-west': { green: ew_time, yellow: YELLOW_TIME, red: red_ew }
  };

  console.log(`[GET /api/latest-timings] 🔄 Sent to frontend:
  NS Vehicles: ${latestData.input.ns_vehicles}, EW Vehicles: ${latestData.input.ew_vehicles}
  NS Green=${ns_time}s | EW Green=${ew_time}s`);

  res.json(response);
});

// --- Start the server ---
app.listen(PORT, () => {
  console.log(`🚦 Smart Traffic Backend running on: http://localhost:${PORT}`);
  console.log('📡 Endpoints:');
  console.log('  POST /api/update-counts → from Python CV system');
  console.log('  GET  /api/latest-timings → to React frontend');
});
