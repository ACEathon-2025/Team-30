// backend/server.js

const express = require('express');
const { spawn } = require('child_process');
const cors = require('cors');

const app = express();
const PORT = 5001; // Using a port like 5001 to avoid conflicts

// --- Middleware ---
app.use(cors()); // Enable Cross-Origin Resource Sharing
app.use(express.json()); // Enable parsing of JSON request bodies

/**
 * A helper function to run the Python prediction script.
 * @param {number} vehicleCount - The number of vehicles to pass to the script.
 * @returns {Promise<number>} - A promise that resolves with the calculated green light time.
 */
const getGreenTimeFromModel = (vehicleCount) => {
    return new Promise((resolve, reject) => {
        // Spawn a new child process to run the Python script
        // The path to the script is relative to the backend folder
        const pythonProcess = spawn('python', ['../ml/predictor.py', vehicleCount]);

        let result = '';
        let error = '';

        // Listen for data output from the script
        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        // Listen for any errors from the script
        pythonProcess.stderr.on('data', (data) => {
            error += data.toString();
        });

        // Handle the script finishing
        pythonProcess.on('close', (code) => {
            if (code !== 0 || error) {
                console.error(`Python script error: ${error}`);
                return reject(new Error('Failed to get prediction from model.'));
            }
            // Parse the integer result and resolve the promise
            resolve(parseInt(result.trim(), 10));
        });
    });
};


// --- API Endpoint ---
app.post('/api/signal-timings', async (req, res) => {
    const { ns_vehicles, ew_vehicles } = req.body;

    // --- Input Validation ---
    if (ns_vehicles === undefined || ew_vehicles === undefined) {
        return res.status(400).json({ error: 'Missing vehicle counts for ns_vehicles or ew_vehicles.' });
    }

    try {
        console.log(`Received request: NS=${ns_vehicles}, EW=${ew_vehicles}`);

        // --- Get Predictions Concurrently ---
        // Run both predictions at the same time for efficiency
        const [green_ns, green_ew] = await Promise.all([
            getGreenTimeFromModel(ns_vehicles),
            getGreenTimeFromModel(ew_vehicles)
        ]);
        
        console.log(`Model predictions: Green NS=${green_ns}s, Green EW=${green_ew}s`);

        // --- Calculate Full Signal Cycle ---
        const YELLOW_TIME = 4; // Fixed yellow light duration
        const red_ns = green_ew + YELLOW_TIME;
        const red_ew = green_ns + YELLOW_TIME;

        const timings = {
            'north-south': { green: green_ns, yellow: YELLOW_TIME, red: red_ns },
            'east-west': { green: green_ew, yellow: YELLOW_TIME, red: red_ew }
        };

        // --- Send Response ---
        res.json(timings);

    } catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({ error: 'An internal server error occurred.' });
    }
});


// --- Start the Server ---
app.listen(PORT, () => {
    console.log(`Backend server is running on http://localhost:${PORT}`);
    console.log('Waiting for requests...');
});
