// diagnostics.js - System for logging, screenshotting, and versioning.

class DiagnosticLogger {
    constructor() {
        this.active = false;
        this.codeHash = null;
        this.screenshots = [];
        this.consoleLogs = [];
        this.originalConsole = {};
        this.canvasesToCapture = [];
        this.lfoPeriod = 5000; // Default LFO period in milliseconds (e.g., 5 seconds)
        this.lfoIntervalId = null;
        this.lfoIndicatorLamp = null; // Reference to the indicator lamp element
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
        this.lfoIndicatorLamp = document.getElementById('lfo-indicator-lamp');
        this.startLFO(); // Automatically start LFO
    }

    startLFO() {
        if (this.lfoIntervalId) {
            this.originalConsole.warn("LFO is already running.");
            return;
        }
        this.originalConsole.log(`Starting LFO with period: ${this.lfoPeriod}ms`);
        this._updateLFOIndicator('green'); // Set lamp to green when LFO starts
        this.lfoIntervalId = setInterval(() => {
            this.captureFrame();
        }, this.lfoPeriod);
    }

    stopLFO() {
        if (this.lfoIntervalId) {
            this.originalConsole.log("Stopping LFO.");
            clearInterval(this.lfoIntervalId);
            this.lfoIntervalId = null;
            this._updateLFOIndicator('gray'); // Set lamp to gray when LFO stops
        }
    }

    _updateLFOIndicator(color) {
        if (this.lfoIndicatorLamp) {
            this.lfoIndicatorLamp.style.backgroundColor = color;
        }
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

    async captureFrame() {
        if (!this.active) {
            this.originalConsole.error("Logger not active. Cannot capture frame.");
            return;
        }

        const timestamp = new Date().toISOString();
        let dataUrl = null;

        try {
            const canvas = await html2canvas(document.documentElement, { 
                useCORS: true, 
                logging: false, 
                scale: window.devicePixelRatio 
            });
            dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        } catch (error) {
            this.originalConsole.error("Error capturing full page screenshot:", error);
            // Fallback to capturing only canvases if full page capture fails
            const canvases = this.canvasesToCapture().filter(c => c && c.width > 1 && c.height > 1);
            if (canvases.length === 0) {
                this.originalConsole.warn("No visible canvases to capture as fallback.");
                return;
            }

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
            dataUrl = tempCanvas.toDataURL('image/jpeg', 0.7);
        }

        this.screenshots.push({
            timestamp,
            filename: `seq_${this.codeHash}_${this.screenshots.length}.jpeg`,
            dataUrl: dataUrl
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

    async generateAndDownload() {
        if (!this.active) {
            this.originalConsole.error("Logger not active.");
            return;
        }
        this.originalConsole.log("Sending log files to server...");

        // 1. Send screenshots
        await Promise.all(this.screenshots.map(ss => {
            return this._sendToServer({ type: 'screenshot', filename: ss.filename, payload: ss.dataUrl });
        }));

        // 2. Send console log file
        const logText = this.consoleLogs.map(l => `[${l.timestamp}] [${l.level.toUpperCase()}] ${l.message}`).join('\n');
        await this._sendToServer({ type: 'log', filename: `log_${this.codeHash}.txt`, payload: logText });

        // 3. Send metadata JSON
        const metadata = {
            codeHash: this.codeHash,
            sessionTimestamp: new Date().toISOString(),
            screenshots: this.screenshots.map(ss => ({ timestamp: ss.timestamp, filename: ss.filename })),
            console: this.consoleLogs
        };
        await this._sendToServer({ type: 'metadata', filename: `meta_${this.codeHash}_${new Date().getTime()}.json`, payload: JSON.stringify(metadata, null, 2) });

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