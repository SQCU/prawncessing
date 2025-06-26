// diagnostics.js - System for logging, screenshotting, and versioning.

class DiagnosticLogger {
    constructor() {
        this.active = false;
        this.codeHash = null;
        this.screenshots = [];
        this.consoleLogs = [];
        this.originalConsole = {};
        this.canvasesToCapture = [];
    }

    async initialize(jsFiles, canvasGetters) {
        if (this.active) {
            console.warn("Logger is already active.");
            return;
        }
        console.log("Initializing logger...");
        this.canvasesToCapture = canvasGetters;
        this._interceptConsole();
        this.codeHash = await this._generateCodeHash(jsFiles);
        this.active = true;
        console.log(`Logger active. Code hash: ${this.codeHash}`);
    }

    _hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = (hash << 5) - hash + char;
            hash |= 0; // Convert to 32bit integer
        }
        return (hash >>> 0).toString(16).padStart(8, '0');
    }

    async _generateCodeHash(files) {
        try {
            const contents = await Promise.all(
                files.map(url => fetch(url).then(res => {
                    if (!res.ok) throw new Error(`Failed to fetch ${url}`);
                    return res.text();
                }))
            );
            const combined = contents.join('\n--- FILE SEPARATOR ---\n');
            return this._hashCode(combined);
        } catch (error) {
            console.error("Error generating code hash:", error);
            return 'error-hashing';
        }
    }

    _interceptConsole() {
        const levels = ['log', 'warn', 'error', 'info', 'debug'];
        levels.forEach(level => {
            this.originalConsole[level] = console[level];
            console[level] = (...args) => {
                if (this.active) {
                    this.consoleLogs.push({
                        level,
                        timestamp: new Date().toISOString(),
                        message: args.map(arg => this._argToString(arg)).join(' '),
                    });
                }
                this.originalConsole[level].apply(console, args);
            };
        });
    }

    _argToString(arg) {
        if (arg instanceof Error) return arg.stack;
        if (typeof arg === 'object' && arg !== null) return JSON.stringify(arg, null, 2);
        return String(arg);
    }

    captureFrame() {
        if (!this.active) {
            this.originalConsole.error("Logger not active. Cannot capture frame.");
            return;
        }

        const canvases = this.canvasesToCapture().filter(c => c && c.width > 1 && c.height > 1);
        if (canvases.length === 0) {
            this.originalConsole.warn("No visible canvases to capture.");
            return;
        }

        // Create a temporary canvas to stitch them together
        const totalWidth = Math.max(...canvases.map(c => c.width));
        const totalHeight = canvases.reduce((sum, c) => sum + c.height, 0);
        const tempCanvas = document.createElement('canvas');
        const ctx = tempCanvas.getContext('2d');
        tempCanvas.width = totalWidth;
        tempCanvas.height = totalHeight;
        ctx.fillStyle = '#333';
        ctx.fillRect(0, 0, totalWidth, totalHeight);

        let yOffset = 0;
        canvases.forEach(c => {
            ctx.drawImage(c, 0, yOffset);
            yOffset += c.height;
        });

        const timestamp = new Date().toISOString();
        this.screenshots.push({
            timestamp,
            filename: `seq_${this.codeHash}_${this.screenshots.length}.png`,
            dataUrl: tempCanvas.toDataURL('image/png')
        });
        this.originalConsole.log(`Captured frame ${this.screenshots.length}.`);
    }

    async _sendToServer(data) {
        try {
            const response = await fetch('/savelog', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
        } catch (error) {
            this.originalConsole.error(`Failed to send data to server: ${error.message}`);
        }
    }

    generateAndDownload() {
        if (!this.active) {
            this.originalConsole.error("Logger not active.");
            return;
        }
        this.originalConsole.log("Sending log files to server...");

        // 1. Send screenshots
        this.screenshots.forEach(ss => {
            this._sendToServer({ type: 'screenshot', filename: ss.filename, payload: ss.dataUrl });
        });

        // 2. Send console log file
        const logText = this.consoleLogs.map(l => `[${l.timestamp}] [${l.level.toUpperCase()}] ${l.message}`).join('\n');
        this._sendToServer({ type: 'log', filename: `log_${this.codeHash}.txt`, payload: logText });

        // 3. Send metadata JSON
        const metadata = {
            codeHash: this.codeHash,
            sessionTimestamp: new Date().toISOString(),
            screenshots: this.screenshots.map(ss => ({ timestamp: ss.timestamp, filename: ss.filename })),
            console: this.consoleLogs
        };
        this._sendToServer({ type: 'metadata', filename: `meta_${this.codeHash}.json`, payload: JSON.stringify(metadata, null, 2) });

        // Reset for next session
        this._reset();
    }
    
    _reset() {
        this.active = false;
        this.screenshots = [];
        this.consoleLogs = [];
        Object.keys(this.originalConsole).forEach(level => {
            if (this.originalConsole[level]) {
                console[level] = this.originalConsole[level];
            }
        });
        this.originalConsole = {};
    }
}