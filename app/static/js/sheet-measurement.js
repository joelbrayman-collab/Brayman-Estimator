/**
 * Sheet Measurement & Scale Calibration Controller (M010 / ADR-027)
 * Handles PDF rendering via PDF.js, SVG overlay, normalized coordinates, and interactive tools.
 */

(function () {
    const config = window.PLAN_CONFIG || {};
    const container = document.getElementById("viewer-container");
    const stage = document.getElementById("drawing-stage");
    const canvas = document.getElementById("pdf-canvas");
    const overlay = document.getElementById("measurement-overlay");
    const loadingText = document.getElementById("viewer-loading");
    const hintText = document.getElementById("interaction-hint");
    const coordsText = document.getElementById("cursor-coords");
    const toolSelect = document.getElementById("tool-select");
    const liveValueText = document.getElementById("live-value-text");
    const liveSubvalueText = document.getElementById("live-subvalue-text");

    let pdfDoc = null;
    let pageNum = (config.pageIndex || 0) + 1; // PDF.js is 1-based
    let scaleFactor = 1.0;
    let currentTool = "pan";
    let isPanning = false;
    let startX = 0, startY = 0;
    let scrollLeft = 0, scrollTop = 0;

    let activePoints = []; // [{x, y}] normalized
    let activeCalRatio = config.activeCalRatio || null;
    let activeCalUnit = config.activeCalUnit || "ft";
    let isNts = config.isNts || false;

    // PDF.js worker setup
    if (window.pdfjsLib) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    }

    // Initialize View & Render
    function init() {
        setupTabs();
        setupTools();
        setupZoomControls();
        setupCanvasEvents();

        if (config.pdfUrl && config.pdfUrl !== "null" && window.pdfjsLib) {
            loadPdf(config.pdfUrl);
        } else {
            drawFallbackGrid();
        }
    }

    function loadPdf(url) {
        loadingText.style.display = "block";
        pdfjsLib.getDocument(url).promise.then(function (pdf) {
            pdfDoc = pdf;
            renderPage(pageNum);
        }).catch(function (err) {
            console.error("Error loading PDF via PDF.js:", err);
            drawFallbackGrid();
        });
    }

    function renderPage(num) {
        if (!pdfDoc) return;
        pdfDoc.getPage(num).then(function (page) {
            const viewport = page.getViewport({ scale: scaleFactor });
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            overlay.setAttribute("viewBox", `0 0 ${viewport.width} ${viewport.height}`);

            const renderContext = {
                canvasContext: canvas.getContext("2d"),
                viewport: viewport
            };

            page.render(renderContext).promise.then(function () {
                loadingText.style.display = "none";
                redrawOverlay();
            });
        });
    }

    function drawFallbackGrid() {
        loadingText.style.display = "none";
        canvas.width = 1000;
        canvas.height = 700;
        overlay.setAttribute("viewBox", `0 0 1000 700`);
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Grid lines
        ctx.strokeStyle = "#e2e8f0";
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 50) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 50) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
        }

        ctx.fillStyle = "#64748b";
        ctx.font = "16px sans-serif";
        ctx.fillText("Plan Sheet Vector Stage", 40, 50);
        redrawOverlay();
    }

    // Normalized Coordinate Helpers
    function getNormalizedCoords(evt) {
        const rect = overlay.getBoundingClientRect();
        const clientX = evt.clientX;
        const clientY = evt.clientY;
        const normX = Math.max(0.0, Math.min(1.0, (clientX - rect.left) / rect.width));
        const normY = Math.max(0.0, Math.min(1.0, (clientY - rect.top) / rect.height));
        return { x: parseFloat(normX.toFixed(5)), y: parseFloat(normY.toFixed(5)) };
    }

    function normToSvg(pt) {
        const w = canvas.width || 1000;
        const h = canvas.height || 700;
        return { x: pt.x * w, y: pt.y * h };
    }

    // Geometry Calculations (Client-Side)
    function calcDistance(p1, p2) {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function updateLiveValues() {
        if (!liveValueText) return;

        if (isNts) {
            liveValueText.innerText = "NTS";
            liveSubvalueText.innerText = "Drawing is flagged Not To Scale";
            return;
        }

        if (activePoints.length === 0) {
            liveValueText.innerText = "—";
            liveSubvalueText.innerText = "";
            return;
        }

        if (currentTool === "two_point_cal") {
            if (activePoints.length === 2) {
                const normD = calcDistance(activePoints[0], activePoints[1]);
                liveValueText.innerText = `${(normD * 100).toFixed(2)}% of canvas`;
                liveSubvalueText.innerText = "Enter known distance in sidebar";
                document.getElementById("cal-p1-x").value = activePoints[0].x;
                document.getElementById("cal-p1-y").value = activePoints[0].y;
                document.getElementById("cal-p2-x").value = activePoints[1].x;
                document.getElementById("cal-p2-y").value = activePoints[1].y;
                document.getElementById("btn-save-2pt-cal").disabled = false;
            }
            return;
        }

        if (!activeCalRatio) {
            liveValueText.innerText = "Uncalibrated";
            liveSubvalueText.innerText = "Please calibrate scale before measuring";
            return;
        }

        if (currentTool === "linear" && activePoints.length === 2) {
            const normD = calcDistance(activePoints[0], activePoints[1]);
            const val = normD * activeCalRatio;
            liveValueText.innerText = `${val.toFixed(2)} ${activeCalUnit}`;
            liveSubvalueText.innerText = `Linear Distance (${(normD).toFixed(4)} norm)`;
            enableSaveMeasurement("linear", activePoints, val);
        } else if (currentTool === "polyline" && activePoints.length >= 2) {
            let totalNorm = 0;
            for (let i = 0; i < activePoints.length - 1; i++) {
                totalNorm += calcDistance(activePoints[i], activePoints[i + 1]);
            }
            const val = totalNorm * activeCalRatio;
            liveValueText.innerText = `${val.toFixed(2)} ${activeCalUnit}`;
            liveSubvalueText.innerText = `Polyline (${activePoints.length} points)`;
            enableSaveMeasurement("polyline", activePoints, val);
        } else if (currentTool === "area" && activePoints.length >= 3) {
            let accum = 0;
            let periNorm = 0;
            const n = activePoints.length;
            for (let i = 0; i < n; i++) {
                const p1 = activePoints[i];
                const p2 = activePoints[(i + 1) % n];
                accum += p1.x * p2.y - p2.x * p1.y;
                periNorm += calcDistance(p1, p2);
            }
            const normArea = 0.5 * Math.abs(accum);
            const realArea = normArea * (activeCalRatio * activeCalRatio);
            const realPeri = periNorm * activeCalRatio;
            const areaUnit = activeCalUnit.startsWith("sq_") ? activeCalUnit : `sq_${activeCalUnit}`;
            liveValueText.innerText = `${realArea.toFixed(2)} ${areaUnit}`;
            liveSubvalueText.innerText = `Perimeter: ${realPeri.toFixed(2)} ${activeCalUnit}`;
            enableSaveMeasurement("area", activePoints, realArea);
        } else if (currentTool === "count" && activePoints.length >= 1) {
            liveValueText.innerText = `${activePoints.length}`;
            liveSubvalueText.innerText = `Point count marker`;
            enableSaveMeasurement("count", activePoints, activePoints.length);
        }
    }

    function enableSaveMeasurement(type, points, val) {
        document.getElementById("meas-type-input").value = type;
        document.getElementById("meas-geometry-input").value = JSON.stringify(points);
        document.getElementById("btn-save-measurement").disabled = false;
    }

    // SVG Drawing Overlays
    function redrawOverlay() {
        overlay.innerHTML = "";

        if (activePoints.length > 0) {
            const svgPoints = activePoints.map(normToSvg);

            // Draw line / polygon
            if (currentTool === "linear" || currentTool === "two_point_cal") {
                if (svgPoints.length === 2) {
                    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    line.setAttribute("x1", svgPoints[0].x);
                    line.setAttribute("y1", svgPoints[0].y);
                    line.setAttribute("x2", svgPoints[1].x);
                    line.setAttribute("y2", svgPoints[1].y);
                    line.setAttribute("stroke", currentTool === "two_point_cal" ? "#f59e0b" : "#3b82f6");
                    line.setAttribute("stroke-width", "3");
                    line.setAttribute("stroke-dasharray", currentTool === "two_point_cal" ? "6,4" : "none");
                    overlay.appendChild(line);
                }
            } else if (currentTool === "polyline") {
                const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
                const ptsStr = svgPoints.map(p => `${p.x},${p.y}`).join(" ");
                polyline.setAttribute("points", ptsStr);
                polyline.setAttribute("stroke", "#3b82f6");
                polyline.setAttribute("stroke-width", "3");
                polyline.setAttribute("fill", "none");
                overlay.appendChild(polyline);
            } else if (currentTool === "area") {
                const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                const ptsStr = svgPoints.map(p => `${p.x},${p.y}`).join(" ");
                polygon.setAttribute("points", ptsStr);
                polygon.setAttribute("stroke", "#10b981");
                polygon.setAttribute("stroke-width", "2");
                polygon.setAttribute("fill", "rgba(16, 185, 129, 0.25)");
                overlay.appendChild(polygon);
            }

            // Draw Point Markers
            svgPoints.forEach((pt, idx) => {
                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", pt.x);
                circle.setAttribute("cy", pt.y);
                circle.setAttribute("r", "5");
                circle.setAttribute("fill", "#ef4444");
                circle.setAttribute("stroke", "#ffffff");
                circle.setAttribute("stroke-width", "2");
                overlay.appendChild(circle);
            });
        }
    }

    // Events & Interactivity
    function setupCanvasEvents() {
        overlay.addEventListener("mousemove", function (e) {
            const coords = getNormalizedCoords(e);
            coordsText.innerText = `X: ${coords.x.toFixed(4)}, Y: ${coords.y.toFixed(4)} (norm)`;

            if (isPanning) {
                container.scrollLeft = scrollLeft - (e.clientX - startX);
                container.scrollTop = scrollTop - (e.clientY - startY);
            }
        });

        overlay.addEventListener("mousedown", function (e) {
            if (currentTool === "pan") {
                isPanning = true;
                startX = e.clientX;
                startY = e.clientY;
                scrollLeft = container.scrollLeft;
                scrollTop = container.scrollTop;
                container.style.cursor = "grabbing";
                return;
            }

            const pt = getNormalizedCoords(e);

            if (currentTool === "two_point_cal" || currentTool === "linear") {
                if (activePoints.length >= 2) activePoints = [];
                activePoints.push(pt);
            } else if (currentTool === "polyline" || currentTool === "area" || currentTool === "count") {
                activePoints.push(pt);
            }

            redrawOverlay();
            updateLiveValues();
        });

        window.addEventListener("mouseup", function () {
            if (isPanning) {
                isPanning = false;
                container.style.cursor = currentTool === "pan" ? "grab" : "crosshair";
            }
        });

        document.getElementById("btn-clear-measurement").addEventListener("click", function () {
            activePoints = [];
            redrawOverlay();
            updateLiveValues();
            document.getElementById("btn-save-measurement").disabled = true;
        });

        document.getElementById("btn-start-2pt-cal").addEventListener("click", function () {
            toolSelect.value = "two_point_cal";
            setTool("two_point_cal");
            activePoints = [];
            redrawOverlay();
            updateLiveValues();
        });
    }

    function setupTools() {
        toolSelect.addEventListener("change", function () {
            setTool(this.value);
        });
    }

    function setTool(tool) {
        currentTool = tool;
        activePoints = [];
        redrawOverlay();
        updateLiveValues();

        if (tool === "pan") {
            container.style.cursor = "grab";
            hintText.innerText = "Click and drag on drawing to pan around.";
        } else if (tool === "two_point_cal") {
            container.style.cursor = "crosshair";
            hintText.innerText = "Click two reference points on drawing to calibrate scale.";
        } else if (tool === "linear") {
            container.style.cursor = "crosshair";
            hintText.innerText = "Click 2 points to measure linear distance.";
        } else if (tool === "polyline") {
            container.style.cursor = "crosshair";
            hintText.innerText = "Click multiple points to measure cumulative length.";
        } else if (tool === "area") {
            container.style.cursor = "crosshair";
            hintText.innerText = "Click 3+ points to measure polygon surface area & perimeter.";
        } else if (tool === "count") {
            container.style.cursor = "crosshair";
            hintText.innerText = "Click to place count markers.";
        }
    }

    function setupZoomControls() {
        const zoomText = document.getElementById("zoom-level-text");

        document.getElementById("btn-zoom-in").addEventListener("click", function () {
            scaleFactor = Math.min(3.0, scaleFactor + 0.25);
            zoomText.innerText = `${Math.round(scaleFactor * 100)}%`;
            renderPage(pageNum);
        });

        document.getElementById("btn-zoom-out").addEventListener("click", function () {
            scaleFactor = Math.max(0.25, scaleFactor - 0.25);
            zoomText.innerText = `${Math.round(scaleFactor * 100)}%`;
            renderPage(pageNum);
        });

        document.getElementById("btn-zoom-100").addEventListener("click", function () {
            scaleFactor = 1.0;
            zoomText.innerText = "100%";
            renderPage(pageNum);
        });

        document.getElementById("btn-zoom-fit").addEventListener("click", function () {
            scaleFactor = 0.75;
            zoomText.innerText = "75%";
            renderPage(pageNum);
        });
    }

    function setupTabs() {
        const tab2pt = document.getElementById("tab-2pt");
        const tabPreset = document.getElementById("tab-preset");
        const tabNts = document.getElementById("tab-nts");
        const panel2pt = document.getElementById("panel-2pt");
        const panelPreset = document.getElementById("panel-preset");
        const panelNts = document.getElementById("panel-nts");

        tab2pt.addEventListener("click", function () {
            tab2pt.classList.add("active"); tabPreset.classList.remove("active"); tabNts.classList.remove("active");
            panel2pt.style.display = "block"; panelPreset.style.display = "none"; panelNts.style.display = "none";
        });

        tabPreset.addEventListener("click", function () {
            tabPreset.classList.add("active"); tab2pt.classList.remove("active"); tabNts.classList.remove("active");
            panelPreset.style.display = "block"; panel2pt.style.display = "none"; panelNts.style.display = "none";
        });

        tabNts.addEventListener("click", function () {
            tabNts.classList.add("active"); tab2pt.classList.remove("active"); tabPreset.classList.remove("active");
            panelNts.style.display = "block"; panel2pt.style.display = "none"; panelPreset.style.display = "none";
        });
    }

    // Boot
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
