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

// Basic text normalization to make TTS sound natural
function normalizeForTTS(raw) {
    if (!raw) return "";
    let text = String(raw);

    // 1) Remove markdown formatting (bold/italic/code/strikethrough)
    text = text.replace(/[*_`~]+/g, "");

    // 2) Replace common iconography/emojis with words (keep short and natural)
    const replacements = [
        [/🔄/g, " alternatively, "],
        [/📊/g, " note: "],
        [/🛏️|🛏/g, " beds "],
        [/💰/g, " cost "],
        [/⭐️|⭐/g, " rated "],
    ];
    for (const [pattern, repl] of replacements) text = text.replace(pattern, repl);

    // 3) Ratings like "rated 4.55/5 (76 reviews)" -> "rated 4.55 out of 5 from 76 reviews"
    text = text.replace(/rated\s*(\d+(?:\.\d+)?)\s*\/(\d+)/i, (m, a, b) => `rated ${a} out of ${b}`);
    text = text.replace(/\((\d+)\s*reviews\)/i, (m, n) => ` from ${n} reviews`);

    // 4) "Type BOOK to reserve" -> "Say "book" to reserve"
    text = text.replace(/type\s+book\b/gi, 'say "book"');

    // 5) Replace bullets/dashes with sentence breaks
    text = text.replace(/[•\-]\s+/g, ". ");

    // 6) Remove any remaining standalone emojis/special pictographs (best-effort)
    try {
        // Remove extended pictographic characters
        text = text.replace(/[\p{Extended_Pictographic}\uFE0F]/gu, "");
    } catch (_) {
        // Fallback small set if Unicode property escapes not supported
        text = text.replace(/[\u2600-\u27BF\u1F300-\u1FAFF]/g, "");
    }

    // 7) Tone down exclamation for TTS prosody
    text = text.replace(/!+/g, ".");

    // 8) Collapse excessive whitespace and ensure sentence spacing
    text = text.replace(/\s{2,}/g, " ").trim();

    // 9) Ensure there is a period at end if looks like a sentence list
    if (!/[.!?]$/.test(text)) text += ".";

    return text;
}

// Enable CORS
app.use(cors());

// Streamed TTS via POST (body: { text })
app.post("/tts", express.json(), async (req, res) => {
    let { text } = req.body || {};
    if (!text) return res.status(400).json({ error: "Text input is required." });
    text = normalizeForTTS(text);

    try {
        const dgResponse = await axios.post(
            "https://api.deepgram.com/v1/speak?model=aura-2-thalia-en",
            { text },
            {
                headers: {
                    Authorization: `Token ${DEEPGRAM_API_KEY}`,
                    "Content-Type": "application/json",
                    // Accept smaller, faster-to-stream audio. Deepgram defaults to MP3; adjust if needed.
                    Accept: "audio/mpeg",
                },
                responseType: "stream",
                httpsAgent: keepAliveAgent,
            }
        );

        // Forward headers as appropriate for streaming
        res.setHeader("Content-Type", dgResponse.headers["content-type"] || "audio/mpeg");
        res.setHeader("Cache-Control", "no-store");

        dgResponse.data.on("error", (err) => {
            console.error("Deepgram stream error:", err?.message || err);
            if (!res.headersSent) res.status(502).end();
            else res.destroy(err);
        });

        // Pipe the Deepgram audio stream directly to the client
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

app.get('/', (req, res) => {
    res.send('Welcome to the Ferris Realtime API Server!');
});

// Ensure the HTTP server is defined
const server = http.createServer(app);

server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});