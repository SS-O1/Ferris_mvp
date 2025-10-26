import express from "express";
import cors from "cors";
import http from "http";
import axios from "axios";
import https from "https";

const app = express();
const PORT = 3000;
const DEEPGRAM_API_KEY = "1ed5a7a9fc3732359b2bc702275b3e68ab0fa9a6";

// Reuse TLS connections to Deepgram for faster requests
const keepAliveAgent = new https.Agent({ keepAlive: true });

// Enable CORS
app.use(cors());

// Serve static files from the 'static' directory
app.use(express.static('static'));

app.get('/', (req, res) => {
    res.send('Welcome to the Ferris Realtime API Server!');
});

// Streamed TTS via POST (body: { text })
app.post("/tts", express.json(), async (req, res) => {
    let { text } = req.body || {};
    if (!text) return res.status(400).json({ error: "Text input is required." });

    try {
        const dgResponse = await axios.post(
            "https://api.deepgram.com/v1/speak?model=aura-2-thalia-en",
            { text },
            {
                headers: {
                    Authorization: `Token ${DEEPGRAM_API_KEY}`,
                    "Content-Type": "application/json",
                    Accept: "audio/mpeg",
                },
                responseType: "stream",
                httpsAgent: keepAliveAgent,
            }
        );

        res.setHeader("Content-Type", dgResponse.headers["content-type"] || "audio/mpeg");
        res.setHeader("Cache-Control", "no-store");

        dgResponse.data.on("error", (err) => {
            console.error("Deepgram stream error:", err?.message || err);
            if (!res.headersSent) res.status(502).end();
            else res.destroy(err);
        });

        dgResponse.data.pipe(res);
    } catch (error) {
        console.error("Error with Deepgram TTS:", error.response?.data || error.message);
        res.status(500).json({ error: "Failed to process text-to-speech." });
    }
});

// Streamed TTS via GET (/tts?text=...)
app.get("/tts", async (req, res) => {
    let text = req.query.text;
    if (!text || typeof text !== "string") {
        return res.status(400).json({ error: "Query param 'text' is required." });
    }
    text = normalizeForTTS(text);

    try {
        const dgResponse = await axios.post(
            "https://api.deepgram.com/v1/speak?model=aura-2-thalia-en",
            { text },
            {
                headers: {
                    Authorization: `Token ${DEEPGRAM_API_KEY}`,
                    "Content-Type": "application/json",
                    Accept: "audio/mpeg",
                },
                responseType: "stream",
                httpsAgent: keepAliveAgent,
            }
        );

        res.setHeader("Content-Type", dgResponse.headers["content-type"] || "audio/mpeg");
        res.setHeader("Cache-Control", "no-store");

        dgResponse.data.on("error", (err) => {
            console.error("Deepgram stream error:", err?.message || err);
            if (!res.headersSent) res.status(502).end();
            else res.destroy(err);
        });

        dgResponse.data.pipe(res);
    } catch (error) {
        console.error("Error with Deepgram TTS:", error.response?.data || error.message);
        res.status(500).json({ error: "Failed to process text-to-speech." });
    }
});

function normalizeForTTS(text) {
    return text.trim().replace(/\s+/g, ' ').replace(/([a-zA-Z])$/, '$1.');
}

const server = http.createServer(app);

server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
