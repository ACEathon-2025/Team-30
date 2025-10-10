const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 5001;

app.use(cors());
app.use(express.json());

let latestData = {
  input: { ns_vehicles: 0, ew_vehicles: 0 },
  timings: { ns_time: 10, ew_time: 10 }
};

function updateSignalTimings(ns_count, ew_count) {
  const computeGreenTime = count => Math.min(Math.max(10, count * 5), 60);
  latestData.timings.ns_time = computeGreenTime(ns_count);
  latestData.timings.ew_time = computeGreenTime(ew_count);
}

// POST endpoint to receive counts from Python CV client
app.post('/api/update-counts', (req, res) => {
  const { ns_vehicles, ew_vehicles } = req.body;
  if (ns_vehicles === undefined || ew_vehicles === undefined) {
    return res.status(400).json({ error: "Missing ns_vehicles or ew_vehicles" });
  }

  latestData.input.ns_vehicles = parseInt(ns_vehicles, 10);
  latestData.input.ew_vehicles = parseInt(ew_vehicles, 10);

  updateSignalTimings(latestData.input.ns_vehicles, latestData.input.ew_vehicles);

  console.log(`[POST /api/update-counts] Updated counts - NS: ${latestData.input.ns_vehicles}, EW: ${latestData.input.ew_vehicles}
    NS Green: ${latestData.timings.ns_time}s, EW Green: ${latestData.timings.ew_time}s`);

  res.status(200).json({ message: "Counts updated successfully", data: latestData });
});

// GET endpoint to provide latest counts + timings to frontend
app.get('/api/latest-timings', (req, res) => {
  const YELLOW_TIME = 4;
  const { ns_time, ew_time } = latestData.timings;

  const red_ns = ew_time + YELLOW_TIME;
  const red_ew = ns_time + YELLOW_TIME;

  res.json({
    input: latestData.input,
    'north-south': { green: ns_time, yellow: YELLOW_TIME, red: red_ns },
    'east-west': { green: ew_time, yellow: YELLOW_TIME, red: red_ew },
  });
});

app.listen(PORT, () => {
  console.log(`🚦 Backend running on http://localhost:${PORT}`);
  console.log("POST /api/update-counts from Python CV system");
  console.log("GET  /api/latest-timings to React frontend");
});
