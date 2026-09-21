const API_URL = "http://127.0.0.1:8000";


/* =========================
   DASHBOARD
========================= */

async function loadDashboard() {

    try {

        const response = await fetch(`${API_URL}/audit`);

        if (!response.ok) {
            throw new Error("Dashboard API failed");
        }

        const data = await response.json();

        const summary = data.summary || {};

        const total =
            summary.total_emissions_kg_co2e || 0;

        const scope1 =
            summary.scope_1_kg_co2e || 0;

        const scope2 =
            summary.scope_2_kg_co2e || 0;

        const scope3 =
            summary.scope_3_kg_co2e || 0;


        document.getElementById("totalEmissions").textContent =
            Number(total).toFixed(2);

        document.getElementById("scope1").textContent =
            Number(scope1).toFixed(2);

        document.getElementById("scope2").textContent =
            Number(scope2).toFixed(2);

        document.getElementById("scope3").textContent =
            Number(scope3).toFixed(2);


        const records =
            data.records || [];

        document.getElementById("recordsProcessed").textContent =
            records.length;


        const verified =
            records.filter(
                record => record.status === "VERIFIED"
            ).length;

        const review =
            records.filter(
                record => record.status !== "VERIFIED"
            ).length;


        document.getElementById("verifiedRecords").textContent =
            verified;

        document.getElementById("reviewRecords").textContent =
            review;


        updateBars(
            scope1,
            scope2,
            scope3
        );

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }
}


/* =========================
   EMISSION BARS
========================= */

function updateBars(
    scope1,
    scope2,
    scope3
) {

    const values = [
        Number(scope1) || 0,
        Number(scope2) || 0,
        Number(scope3) || 0
    ];

    const total =
        values[0] +
        values[1] +
        values[2];


    let p1 = 0;
    let p2 = 0;
    let p3 = 0;


    if (total > 0) {

        p1 = (values[0] / total) * 100;
        p2 = (values[1] / total) * 100;
        p3 = (values[2] / total) * 100;

    }


    document.getElementById("scope1Bar").style.width =
        `${p1}%`;

    document.getElementById("scope2Bar").style.width =
        `${p2}%`;

    document.getElementById("scope3Bar").style.width =
        `${p3}%`;


    document.getElementById("scope1BarValue").textContent =
        `${values[0].toFixed(2)} kg`;

    document.getElementById("scope2BarValue").textContent =
        `${values[1].toFixed(2)} kg`;

    document.getElementById("scope3BarValue").textContent =
        `${values[2].toFixed(2)} kg`;
}


/* =========================
   FILE UPLOAD
========================= */

async function uploadDataFile() {

    const fileInput =
        document.getElementById("dataFile");

    const resultBox =
        document.getElementById("uploadResult");

    if (!fileInput.files.length) {

        resultBox.innerHTML = `
            <div class="result-box warning-box">
                Please select a PDF or CSV file.
            </div>
        `;

        return;
    }


    const file =
        fileInput.files[0];


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    resultBox.innerHTML = `
        <div class="result-box">
            Processing <strong>${file.name}</strong>...
        </div>
    `;


    try {

        const response =
            await fetch(
                `${API_URL}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Upload failed"
            );

        }


        if (
            data.status === "SUCCESS"
        ) {

            resultBox.innerHTML = `
                <div class="result-box success-box">

                    <h3>✅ Upload Successful</h3>

                    <p>
                        <strong>File:</strong>
                        ${data.filename || file.name}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        ${data.calculation_status || "Processed"}
                    </p>

                    <p>
                        <strong>Scope:</strong>
                        ${data.scope || "Multiple"}
                    </p>

                    <p>
                        <strong>CO₂e:</strong>
                        ${data.emissions_kg_co2e ?? "See audit trail"}
                        kg
                    </p>

                </div>
            `;

        } else {

            resultBox.innerHTML = `
                <div class="result-box warning-box">

                    <h3>⚠️ Review Required</h3>

                    <p>
                        ${data.message ||
                        "The uploaded data requires verification."}
                    </p>

                </div>
            `;
        }


        await loadDashboard();
        await loadAudit();

    } catch (error) {

        console.error(error);

        resultBox.innerHTML = `
            <div class="result-box error-box">

                <h3>❌ Upload Error</h3>

                <p>
                    ${error.message}
                </p>

            </div>
        `;
    }
}


/* =========================
   MANUAL CALCULATION
========================= */

async function calculateEmission() {

    const activity =
        document.getElementById("activity").value.trim();

    const quantity =
        Number(
            document.getElementById("quantity").value
        );

    const unit =
        document.getElementById("unit").value.trim();


    const resultBox =
        document.getElementById("calculationResult");


    if (!activity || !quantity || !unit) {

        resultBox.innerHTML = `
            <div class="result-box warning-box">
                Please enter activity, quantity and unit.
            </div>
        `;

        return;
    }


    resultBox.innerHTML = `
        <div class="result-box">
            Calculating...
        </div>
    `;


    try {

        const response =
            await fetch(
                `${API_URL}/calculate`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        activity: activity,
                        quantity: quantity,
                        unit: unit
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            const message =
                data.detail?.message ||
                data.detail ||
                "Calculation requires verification.";

            resultBox.innerHTML = `
                <div class="result-box warning-box">

                    <h3>⚠️ Review Required</h3>

                    <p>${message}</p>

                </div>
            `;

            return;
        }


        resultBox.innerHTML = `
            <div class="result-box success-box">

                <h3>✅ Calculation Verified</h3>

                <p>
                    <strong>Activity:</strong>
                    ${data.activity}
                </p>

                <p>
                    <strong>Scope:</strong>
                    ${data.scope}
                </p>

                <p>
                    <strong>Quantity:</strong>
                    ${data.quantity}
                    ${data.unit}
                </p>

                <p>
                    <strong>Emission Factor:</strong>
                    ${data.factor}
                </p>

                <p>
                    <strong>Source:</strong>
                    ${data.factor_source}
                </p>

                <p>
                    <strong>CO₂e:</strong>
                    ${data.emissions_kg_co2e}
                    kg CO₂e
                </p>

                <div class="formula-box">

                    <span>Calculation Formula</span>

                    <strong>
                        ${data.formula}
                    </strong>

                </div>

            </div>
        `;


        await loadDashboard();
        await loadAudit();

    } catch (error) {

        console.error(error);

        resultBox.innerHTML = `
            <div class="result-box error-box">
                ${error.message}
            </div>
        `;
    }
}


/* =========================
   LYZR AI ANALYSIS
========================= */

async function runAIAnalysis() {

    const activity =
        document
            .getElementById("aiActivity")
            .value
            .trim();

    const quantity =
        Number(
            document.getElementById("aiQuantity").value
        );

    const unit =
        document
            .getElementById("aiUnit")
            .value
            .trim();


    const resultBox =
        document.getElementById("aiResult");


    if (!activity || !quantity || !unit) {

        resultBox.innerHTML = `
            <div class="result-box warning-box">

                Please enter activity, quantity and unit.

            </div>
        `;

        return;
    }


    resultBox.innerHTML = `
        <div class="result-box">
            🤖 Lyzr AI is analyzing the activity...
        </div>
    `;


    try {

        const response =
            await fetch(
                `${API_URL}/ai-analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        activity: activity,
                        quantity: quantity,
                        unit: unit
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail?.message ||
                data.detail ||
                "AI analysis failed"
            );
        }


        resultBox.innerHTML = `
            <div class="result-box success-box">

                <h3>🤖 Lyzr AI Analysis</h3>

                <div class="ai-response">
                    ${escapeHtml(
                        data.ai_analysis || ""
                    )}
                </div>

            </div>
        `;

    } catch (error) {

        console.error(error);

        resultBox.innerHTML = `
            <div class="result-box error-box">

                <h3>❌ AI Analysis Error</h3>

                <p>
                    ${escapeHtml(error.message)}
                </p>

            </div>
        `;
    }
}


/* =========================
   AUDIT TRAIL
========================= */

async function loadAudit() {

    const container =
        document.getElementById("auditRecords");


    try {

        const response =
            await fetch(
                `${API_URL}/audit`
            );


        const data =
            await response.json();


        const records =
            data.records || [];


        if (!records.length) {

            container.innerHTML = `
                <div class="empty-state">

                    No audit records yet.

                    <br><br>

                    Upload a document or perform
                    a verified calculation.

                </div>
            `;

            return;
        }


        container.innerHTML =
            records.map(record => {

                const emissions =
                    Number(
                        record.emissions_kg_co2e || 0
                    ).toFixed(4);


                return `

                    <div class="evidence-card">

                        <div class="evidence-header">

                            <div>

                                <h3>
                                    ${escapeHtml(
                                        record.activity || "Unknown Activity"
                                    )}
                                </h3>

                                <span class="scope-badge">
                                    ${escapeHtml(
                                        record.scope || "UNCLASSIFIED"
                                    )}
                                </span>

                            </div>


                            <div class="emission-value">

                                ${emissions}

                                <span>
                                    kg CO₂e
                                </span>

                            </div>

                        </div>


                        <div class="evidence-grid">

                            <div class="evidence-item">

                                <span>
                                    Quantity
                                </span>

                                <strong>
                                    ${record.quantity}
                                    ${escapeHtml(record.unit || "")}
                                </strong>

                            </div>


                            <div class="evidence-item">

                                <span>
                                    Emission Factor
                                </span>

                                <strong>
                                    ${record.factor}
                                </strong>

                            </div>


                            <div class="evidence-item">

                                <span>
                                    Factor Source
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        record.factor_source || "Unknown"
                                    )}
                                </strong>

                            </div>


                            <div class="evidence-item">

                                <span>
                                    Factor Year
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        record.factor_year || "Unknown"
                                    )}
                                </strong>

                            </div>


                            <div class="evidence-item">

                                <span>
                                    Status
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        record.status || "Unknown"
                                    )}
                                </strong>

                            </div>


                            <div class="evidence-item">

                                <span>
                                    Source File
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        record.source_file ||
                                        "Manual Calculation"
                                    )}
                                </strong>

                            </div>

                        </div>


                        <div class="formula-box">

                            <span>
                                Deterministic Calculation
                            </span>

                            <strong>
                                ${escapeHtml(
                                    record.formula || ""
                                )}
                            </strong>

                        </div>


                        <div class="evidence-footer">

                            <span>
                                Audit Record ID:
                                <strong>
                                    #${record.id}
                                </strong>
                            </span>

                            <span>
                                Created:
                                <strong>
                                    ${escapeHtml(
                                        record.created_at || ""
                                    )}
                                </strong>
                            </span>

                        </div>

                    </div>

                `;

            }).join("");


    } catch (error) {

        console.error(
            "Audit error:",
            error
        );

        container.innerHTML = `
            <div class="result-box error-box">

                Unable to load audit records.

            </div>
        `;
    }
}


/* =========================
   HTML ESCAPE
========================= */

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


/* =========================
   INITIAL LOAD
========================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadDashboard();

        loadAudit();

    }
);