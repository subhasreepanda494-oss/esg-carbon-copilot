const API_URL = "";


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

    const percentages = [p1, p2, p3];
    const barIds = ["scope1Bar", "scope2Bar", "scope3Bar"];
    const kpiFillSelectors = [
        ".scope-one-fill",
        ".scope-two-fill",
        ".scope-three-fill"
    ];

    barIds.forEach((id, index) => {
        const bar = document.getElementById(id);

        if (bar) {
            bar.style.width = `${percentages[index]}%`;
            bar.setAttribute(
                "aria-valuenow",
                percentages[index].toFixed(1)
            );
        }
    });

    kpiFillSelectors.forEach((selector, index) => {
        const fill = document.querySelector(selector);

        if (fill) {
            fill.style.width = `${percentages[index]}%`;
        }
    });


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

            const uploadStatus = getUploadStatus(data);
            const uploadTone = uploadStatus === "VERIFIED"
                ? "success-box"
                : "warning-box";
            const hasFileEmissions =
                data.emissions_kg_co2e !== undefined &&
                data.emissions_kg_co2e !== null;

            const recordsList = data.records || [];
            const processedCount = data.records_processed || recordsList.length;
            const verifiedCount = recordsList.filter(r => r.status === "VERIFIED").length;
            const reviewCount = recordsList.filter(r => r.status === "REVIEW_REQUIRED").length;
            const errorCount = recordsList.filter(r => r.status === "UNVERIFIED").length;
            const dataQuality = processedCount > 0 ? ((verifiedCount / processedCount) * 100).toFixed(1) : 0;

            resultBox.innerHTML = `
                <div class="result-box ${uploadTone}">
                    ${renderStatusBadge(uploadStatus)}
                    <h3>Upload processed</h3>
                    <p><strong>File:</strong> ${escapeHtml(data.filename || file.name)}</p>
                    <p><strong>Records Processed:</strong> ${escapeHtml(processedCount)}</p>
                    <p><strong>Total CO₂e:</strong> ${hasFileEmissions ? escapeHtml(data.emissions_kg_co2e) + ' kg' : 'See audit trail'}</p>
                    <p><strong>Valid Records:</strong> ${verifiedCount}</p>
                    <p><strong>Records requiring review:</strong> ${reviewCount}</p>
                    <p><strong>Records with errors:</strong> ${errorCount}</p>
                    <p><strong>Data Quality:</strong> ${dataQuality}% Verified</p>

                    ${renderFactorProvenance(data)}
                    ${data.message ? `<p>${escapeHtml(data.message)}</p>` : ""}
                </div>
            `;

        } else {

            resultBox.innerHTML = `
                <div class="result-box warning-box">

                    ${renderStatusBadge(data.status || "ERROR")}

                    <h3>Review required</h3>

                    <p>
                        ${escapeHtml(
                            data.message ||
                            "The uploaded data requires verification."
                        )}
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

                ${renderStatusBadge("ERROR")}

                <h3>Upload error</h3>

                <p>
                    ${escapeHtml(error.message)}
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
            const failureStatus =
                data.detail?.status ||
                "REVIEW_REQUIRED";

            resultBox.innerHTML = `
                <div class="result-box warning-box">

                    ${renderStatusBadge(failureStatus)}

                    <h3>Calculation requires review</h3>

                    <p>${escapeHtml(message)}</p>

                </div>
            `;

            return;
        }


        resultBox.innerHTML = `
            <div class="result-box success-box">

                ${renderStatusBadge("VERIFIED")}

                <h3>Calculation verified</h3>

                <p>
                    <strong>Activity:</strong>
                    ${escapeHtml(data.activity)}
                </p>

                <p>
                    <strong>Scope:</strong>
                    ${escapeHtml(data.scope)}
                </p>

                <p>
                    <strong>Quantity:</strong>
                    ${escapeHtml(data.quantity)}
                    ${escapeHtml(data.unit)}
                </p>

                <p>
                    <strong>Emission Factor:</strong>
                    ${escapeHtml(data.factor)}
                </p>

                <p>
                    <strong>Source:</strong>
                    ${escapeHtml(data.factor_source)}
                </p>

                ${renderFactorProvenance(data)}

                <p>
                    <strong>CO₂e:</strong>
                    ${escapeHtml(data.emissions_kg_co2e)} kg CO₂e
                </p>

                <div class="formula-box">

                    <span>Calculation Formula</span>

                    <strong>
                        ${escapeHtml(data.formula)}
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
                ${renderStatusBadge("ERROR")}
                <p>${escapeHtml(error.message)}</p>
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

                ${renderStatusBadge("INFO", "AI ANALYSIS")}

                <h3>Lyzr AI analysis</h3>

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

                ${renderStatusBadge("ERROR")}

                <h3>AI analysis error</h3>

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

let esgAuditRecords = [];
let currentAuditFilter = 'ALL';

async function loadAudit() {
    const tbody = document.getElementById("auditTableBody");

    try {
        const response = await fetch(`${API_URL}/audit`);
        const data = await response.json();
        const records = data.records || [];
        esgAuditRecords = records;

        renderAuditTable();

    } catch (error) {
        console.error("Audit error:", error);
        if(tbody) tbody.innerHTML = `<tr><td colspan="11" class="error-box">Unable to load audit records.</td></tr>`;
    }
}

function renderAuditTable() {
    const tbody = document.getElementById("auditTableBody");
    const searchTerm = (document.getElementById("auditSearch")?.value || "").toLowerCase();

    const filtered = esgAuditRecords.filter(r => {
        if (currentAuditFilter !== 'ALL') {
            const isInvalidFilter = currentAuditFilter === 'UNVERIFIED';
            const matches = isInvalidFilter
                ? (r.status === 'UNVERIFIED' || r.status === 'INVALID')
                : (r.status === currentAuditFilter);
            if (!matches) return false;
        }
        if (searchTerm) {
            const act = (r.activity || "").toLowerCase();
            if (!act.includes(searchTerm)) return false;
        }
        return true;
    });

    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="11" class="empty-state">No audit records match the criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map((record, index) => {
        const emissions = Number(record.emissions_kg_co2e || 0).toFixed(4);
        const reviewReason = record.message || "";
        const category = record.category || "Environmental";
        return `
            <tr onclick="openRecordModal(${index})" style="cursor: pointer;">
                <td>#${record.id || index}</td>
                <td>${escapeHtml(category)}</td>
                <td>${escapeHtml(record.activity || "Unknown Activity")}</td>
                <td>${record.quantity}</td>
                <td>${escapeHtml(record.unit || "")}</td>
                <td>${escapeHtml(record.factor || "")}</td>
                <td>${emissions}</td>
                <td>${escapeHtml(record.source_file || "Manual Calculation")}</td>
                <td>${renderStatusBadge(record.status || "UNVERIFIED")}</td>
                <td>${escapeHtml(reviewReason)}</td>
                <td><button class="button button-quiet" onclick="event.stopPropagation(); openRecordModal(${index})">View Details</button></td>
            </tr>
        `;
    }).join("");
}

function setAuditFilter(filter) {
    currentAuditFilter = filter;
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.remove('active');
        if (b.dataset.filter === filter) b.classList.add('active');
    });
    renderAuditTable();
}

function filterAudit() {
    renderAuditTable();
}

function openRecordModal(index) {
    const record = esgAuditRecords[index];
    if (!record) return;

    const modalBody = document.getElementById("modalBody");
    const modal = document.getElementById("recordModal");

    const emissions = Number(record.emissions_kg_co2e || 0).toFixed(4);
    
    modalBody.innerHTML = `
        <h2>Record Details #${record.id || index}</h2>
        <div class="modal-grid">
            <div class="modal-section">
                <h3>Original Uploaded Values</h3>
                <p><strong>Activity:</strong> ${escapeHtml(record.activity)}</p>
                <p><strong>Quantity:</strong> ${record.quantity} ${escapeHtml(record.unit)}</p>
                <p><strong>Source File:</strong> ${escapeHtml(record.source_file)}</p>
            </div>
            <div class="modal-section">
                <h3>Validation & Audit</h3>
                <p><strong>Status:</strong> ${renderStatusBadge(record.status)}</p>
                <p><strong>Review Reason:</strong> ${escapeHtml(record.message || "N/A")}</p>
                <p><strong>Audit Status:</strong> Logged</p>
                <p><strong>Timestamp:</strong> ${escapeHtml(record.created_at || new Date().toISOString())}</p>
            </div>
            <div class="modal-section" style="grid-column: 1 / -1;">
                <h3>Calculation Transparency</h3>
                <p><strong>Emission Factor Used:</strong> ${escapeHtml(record.factor)} (${escapeHtml(record.factor_source)})</p>
                <p><strong>Formula:</strong> ${escapeHtml(record.formula || "Input × Emission Factor = CO2e")}</p>
                <div class="formula-highlight">
                    ${record.quantity} × ${escapeHtml(record.factor)} = <strong>${emissions} kg CO₂e</strong>
                </div>
            </div>
        </div>
    `;
    modal.style.display = "block";
}

function closeModal() {
    document.getElementById("recordModal").style.display = "none";
}

window.onclick = function(event) {
    const modal = document.getElementById("recordModal");
    if (event.target == modal) {
        closeModal();
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


function renderFactorProvenance(record) {

    const factorVersion = String(
        record?.factor_version || ""
    ).trim();

    const sourceUrl = String(
        record?.source_url || ""
    ).trim();

    const sourceRowId = String(
        record?.source_row_id || ""
    ).trim();

    if (!factorVersion && !sourceUrl && !sourceRowId) {
        return "";
    }

    const sourceMarkup = /^https?:\/\//i.test(sourceUrl)
        ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(sourceUrl)}">Official 2026 flat file</a>`
        : `<strong>${escapeHtml(sourceUrl || "Not recorded")}</strong>`;

    return `
        <div class="provenance-box">
            <span>Factor provenance</span>
            <div class="provenance-meta">
                <span>Version <strong>${escapeHtml(factorVersion || "Not recorded")}</strong></span>
                <span>Source row <strong>${escapeHtml(sourceRowId || "Not recorded")}</strong></span>
                <span>${sourceMarkup}</span>
            </div>
        </div>
    `;
}


function statusToken(status) {

    const normalized = String(
        status || ""
    ).trim().toUpperCase();

    if (
        normalized === "VERIFIED" ||
        normalized === "SUCCESS"
    ) {
        return "verified";
    }

    if (normalized === "REVIEW_REQUIRED") {
        return "review";
    }

    if (normalized === "UNVERIFIED") {
        return "unverified";
    }

    if (normalized === "ERROR") {
        return "error";
    }

    return "info";
}


function statusIcon(token) {

    const icons = {
        verified: "✓",
        review: "!",
        unverified: "?",
        error: "×",
        info: "i"
    };

    return icons[token] || icons.info;
}


function renderStatusBadge(status, label) {

    const normalized = String(
        status || "UNVERIFIED"
    ).trim().toUpperCase();
    const token = statusToken(normalized);
    const displayLabel = label || normalized.replace(
        /_/g,
        " "
    );

    return `
        <span class="status-badge status-${token}">
            <span class="status-badge-icon" aria-hidden="true">
                ${statusIcon(token)}
            </span>
            ${escapeHtml(displayLabel)}
        </span>
    `;
}


function getUploadStatus(data) {

    if (data.calculation_status) {
        return String(
            data.calculation_status
        ).toUpperCase();
    }

    if (Array.isArray(data.records)) {

        if (Number(data.unverified_records) > 0) {
            return "UNVERIFIED";
        }

        if (Number(data.review_required_records) > 0) {
            return "REVIEW_REQUIRED";
        }

        if (data.records.length > 0) {
            return "VERIFIED";
        }
    }

    return data.status === "SUCCESS"
        ? "UNVERIFIED"
        : String(data.status || "ERROR").toUpperCase();
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

let esgData = null;

async function loadESGData() {
    try {
        const response = await fetch(`${API_URL}/dashboard-data`);
        if(response.ok) {
            esgData = await response.json();
            renderDashboardData();
        }
    } catch(e) {
        console.error("Failed to load ESG Data", e);
    }
}

function renderDashboardData() {
    if(!esgData) return;
    
    // Profile
        document.getElementById('companyProfile').innerHTML = `
        <div class="profile-item"><strong>Company Name</strong><span>${esgData.company_name || 'Not provided'}</span></div>
        <div class="profile-item"><strong>Industry</strong><span>${esgData.industry && esgData.industry !== 'Unknown' ? esgData.industry : 'Not provided'}</span></div>
        <div class="profile-item"><strong>Location</strong><span>${esgData.location || 'Not provided'}</span></div>
        <div class="profile-item"><strong>Reporting Year</strong><span>${esgData.reporting_year || 'Not provided'}</span></div>
        <div class="profile-item"><strong>Employees</strong><span>${esgData.employees ? esgData.employees : 'Not provided'}</span></div>
        <div class="profile-item"><strong>Revenue</strong><span>${esgData.revenue && esgData.revenue !== 'N/A' ? esgData.revenue : 'Not provided'}</span></div>
        <div class="profile-item"><strong>Reporting Period</strong><span>${esgData.reporting_period || 'Not provided'}</span></div>
        <div class="profile-item"><strong>Dataset Status</strong><span>${esgData.overall_data_quality > 0 ? 'Data Uploaded' : 'Pending Upload'}</span></div>
    `;

    // Scores (Data Quality)
    document.getElementById('dqOverall').textContent = (esgData.overall_data_quality !== null && esgData.overall_data_quality !== undefined) ? `${esgData.overall_data_quality}%` : 'Pending';
    document.getElementById('dqEnv').textContent = (esgData.environmental_data_quality !== null && esgData.environmental_data_quality !== undefined) ? `${esgData.environmental_data_quality}%` : 'Pending - E dataset not uploaded';
    document.getElementById('dqSoc').textContent = (esgData.social_data_quality !== null && esgData.social_data_quality !== undefined) ? `${esgData.social_data_quality}%` : 'Pending - S dataset not uploaded';
    document.getElementById('dqGov').textContent = (esgData.governance_data_quality !== null && esgData.governance_data_quality !== undefined) ? `${esgData.governance_data_quality}%` : 'Pending - G dataset not uploaded';

    // Scores (Performance)
    const fmtScore = (s) => (s !== null && s !== undefined) ? parseFloat(s).toFixed(1) : null;
    document.getElementById('perfOverall').textContent = fmtScore(esgData.overall_performance) ?? 'Pending';
    document.getElementById('perfEnv').textContent = fmtScore(esgData.environmental_performance) ?? 'Pending - E dataset not uploaded';
    document.getElementById('perfSoc').textContent = fmtScore(esgData.social_performance) ?? 'Pending - S dataset not uploaded';
    document.getElementById('perfGov').textContent = fmtScore(esgData.governance_performance) ?? 'Pending - G dataset not uploaded';

    // Helper for rendering metrics
    const getMetricDetails = (pillar, metricName) => {
        if (!esgData.performance_details || !esgData.performance_details[pillar]) return null;
        return esgData.performance_details[pillar].find(m => m.metric === metricName);
    };

    const renderMetricHTML = (label, val, unit, detail) => {
        if (!detail) {
            return `<div class="metric-card"><h4>${label}</h4><div class="val">${val ?? 'N/A'} ${unit}</div></div>`;
        }
        const direction = detail.lower_is_better ? '↓' : '↑';
        return `
            <div class="metric-card">
                <h4>${label}</h4>
                <div class="val">${val ?? 'N/A'} ${unit}</div>
                <div style="font-size: 0.8rem; color: #555; margin-top: 5px;">
                    Benchmark: ${detail.benchmark} ${unit} <br>
                    Target: ${direction} (Better)
                </div>
            </div>`;
    };

    // Social
    if (esgData.social_performance === null || esgData.social_performance === undefined) {
        document.getElementById('socialMetrics').innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <p>Not available in uploaded dataset. Pending — Social dataset not uploaded.</p>
            </div>
        `;
    } else {
        document.getElementById('socialMetrics').innerHTML = `
            ${renderMetricHTML('Employee Turnover', esgData.employee_turnover_pct, '%', getMetricDetails('Social', 'employee_turnover_pct'))}
            ${renderMetricHTML('Training Hours', esgData.training_hours_per_employee, 'hrs', getMetricDetails('Social', 'training_hours_per_employee'))}
            ${renderMetricHTML('Safety Incidents', esgData.workplace_incidents, '', getMetricDetails('Social', 'workplace_incidents'))}
            ${renderMetricHTML('Diversity (Female %)', esgData.diversity_female_pct, '%', getMetricDetails('Social', 'diversity_female_pct'))}
        `;
    }

    // Governance
    if (esgData.governance_performance === null || esgData.governance_performance === undefined) {
        document.getElementById('governanceMetrics').innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <p>Not available in uploaded dataset. Pending — Governance dataset not uploaded.</p>
            </div>
        `;
    } else {
        document.getElementById('governanceMetrics').innerHTML = `
            ${renderMetricHTML('Independent Board %', esgData.board_independent_pct, '%', getMetricDetails('Governance', 'board_independent_pct'))}
            ${renderMetricHTML('Ethics Incidents', esgData.ethics_incidents, '', getMetricDetails('Governance', 'ethics_incidents'))}
            ${renderMetricHTML('Data Privacy Incidents', esgData.data_privacy_incidents, '', getMetricDetails('Governance', 'data_privacy_incidents'))}
            ${renderMetricHTML('Whistleblower Cases', esgData.whistleblower_cases, '', getMetricDetails('Governance', 'whistleblower_cases'))}
        `;
    }

    // Risks
    if (esgData.risks && esgData.risks.length > 0) {
        document.getElementById('riskList').innerHTML = esgData.risks.map(r => `
            <div class="risk-item risk-${r.severity.toLowerCase()}">
                <strong>${r.category} - ${r.metric} [${r.severity} Risk]</strong>
                <p>${r.reason}. <em>Action: ${r.suggested_action}</em></p>
            </div>
        `).join("");
    } else {
        document.getElementById('riskList').innerHTML = `<p>No risks identified based on uploaded datasets.</p>`;
    }

    // Recs
    if (esgData.recommendations && esgData.recommendations.length > 0) {
        document.getElementById('recList').innerHTML = esgData.recommendations.map(r => `
            <div class="rec-item">
                <strong>${r.area}</strong>
                <p>${r.reason} -> ${r.suggested_action}</p>
                <p class="expected">Expected: ${r.expected_improvement}</p>
            </div>
        `).join("");
    } else {
        document.getElementById('recList').innerHTML = `<p>No recommendations currently available.</p>`;
    }

    renderChart();
}

function renderChart() {
    const ctx = document.getElementById('esgTrendChart');
    if(!ctx) return;
    
    // Check if we have any data to render
    if (!esgData || (esgData.scope1_emissions === 0 && esgData.scope2_emissions === 0 && esgData.scope3_emissions === 0)) {
        ctx.parentNode.innerHTML = `<div style="padding: 20px; text-align: center;"><p>Not available in uploaded dataset</p></div>`;
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Scope 1', 'Scope 2', 'Scope 3'],
            datasets: [
                { 
                    label: 'Emissions (kg CO2e)', 
                    data: [esgData.scope1_emissions, esgData.scope2_emissions, esgData.scope3_emissions], 
                    backgroundColor: ['#2a78d6', '#0f9f76', '#f39c12'] 
                }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadESGData();

    // Navigation
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            document.querySelectorAll('.dashboard-section').forEach(sec => sec.style.display = 'none');
            const targetId = link.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            if(target) target.style.display = 'block';
        });
    });
    
    // Hide all sections except profile initially
    document.querySelectorAll('.dashboard-section').forEach(sec => {
        if(sec.id !== 'profile') sec.style.display = 'none';
    });

    // Report Generate
            document.getElementById('generateReportBtn')?.addEventListener('click', () => {
        if (!esgData) {
            alert('Please wait for data to load or upload a dataset first.');
            return;
        }
        let printDiv = document.getElementById('printReport');
        if (!printDiv) {
            printDiv = document.createElement('div');
            printDiv.id = 'printReport';
            document.body.appendChild(printDiv);
        }
        const data = esgData;
        const fmtScore = (s) => (s !== null && s !== undefined) ? parseFloat(s).toFixed(1) : 'Pending';
        printDiv.innerHTML = `
            <div class="print-container">
                <h1>ESG Carbon Copilot - Professional ESG Report</h1>
                <p><em>This ESG score is a prototype analytical indicator and is not an official ESG rating, certification, regulatory assessment, or investment recommendation.</em></p>
                <hr>
                <h2>1. Executive Summary</h2>
                <p><strong>Overall ESG Performance Score:</strong> ${fmtScore(data.overall_performance)}</p>
                <p><strong>Overall Data Quality Score:</strong> ${fmtScore(data.overall_data_quality)}%</p>
                <h2>2. Company Profile</h2>
                <p><strong>Company Name:</strong> ${data.company_name || 'Not provided'}</p>
                <p><strong>Industry:</strong> ${data.industry || 'Not provided'}</p>
                <p><strong>Reporting Year:</strong> ${data.reporting_year || 'Not provided'}</p>
                <h2>3. ESG Pillar Analysis (Performance)</h2>
                <ul>
                    <li><strong>Environmental Performance:</strong> ${fmtScore(data.environmental_performance)}</li>
                    <li><strong>Social Performance:</strong> ${fmtScore(data.social_performance)}</li>
                    <li><strong>Governance Performance:</strong> ${fmtScore(data.governance_performance)}</li>
                </ul>
                <h2>4. Risks & Recommendations</h2>
                <p>Please refer to the online dashboard for detailed risk breakdowns and AI recommendations.</p>
                <hr>
                <p><em>Generated on ${new Date().toLocaleDateString()}</em></p>
            </div>
        `;
        window.print();
    });
    
    // Demo Mode toggle
    const demoToggle = document.getElementById('demoModeToggle');
    demoToggle?.addEventListener('change', (e) => {
        const warning = document.getElementById('demoWarning');
        if(warning) warning.style.display = e.target.checked ? 'block' : 'none';
    });
});

async function uploadSocialFile() {
    const fileInput = document.getElementById("socialFile");
    const resultBox = document.getElementById("socialUploadResult");

    if (!fileInput.files.length) {
        resultBox.innerHTML = `<div class="result-box warning-box">Please select a CSV file.</div>`;
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    resultBox.innerHTML = `<div class="result-box">Processing...</div>`;
    
    try {
        const response = await fetch(`${API_URL}/upload-social`, { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Upload failed");
        
        if (data.status === "ERROR") {
            resultBox.innerHTML = `<div class="result-box error-box">${escapeHtml(data.message || "Upload failed")}</div>`;
            return;
        }

        const msg = data.message ? `<p>${escapeHtml(data.message)}</p>` : "";
        resultBox.innerHTML = `<div class="result-box success-box">Upload successful! Records processed: ${data.records_processed}${msg}</div>`;
        await loadESGData();
        await loadAudit();
    } catch (e) {
        resultBox.innerHTML = `<div class="result-box error-box">Error: ${escapeHtml(e.message)}</div>`;
    }
}

async function uploadGovernanceFile() {
    const fileInput = document.getElementById("governanceFile");
    const resultBox = document.getElementById("governanceUploadResult");

    if (!fileInput.files.length) {
        resultBox.innerHTML = `<div class="result-box warning-box">Please select a CSV file.</div>`;
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    resultBox.innerHTML = `<div class="result-box">Processing...</div>`;
    
    try {
        const response = await fetch(`${API_URL}/upload-governance`, { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Upload failed");
        
        if (data.status === "ERROR") {
            resultBox.innerHTML = `<div class="result-box error-box">${escapeHtml(data.message || "Upload failed")}</div>`;
            return;
        }

        const msg = data.message ? `<p>${escapeHtml(data.message)}</p>` : "";
        resultBox.innerHTML = `<div class="result-box success-box">Upload successful! Records processed: ${data.records_processed}${msg}</div>`;
        await loadESGData();
        await loadAudit();
    } catch (e) {
        resultBox.innerHTML = `<div class="result-box error-box">Error: ${escapeHtml(e.message)}</div>`;
    }
}

function showScoreDetails(pillar) {
    if (!esgData || !esgData.performance_details || !esgData.performance_details[pillar] || esgData.performance_details[pillar].length === 0) {
        alert(`No performance details are available for ${pillar}. Please upload the relevant dataset first.`);
        return;
    }

    const details = esgData.performance_details[pillar];
    const escape = (value) => escapeHtml(String(value ?? "—"));
    const totalWeight = details.reduce((total, detail) => total + Number(detail.weight || 0), 0);
    const totalScore = details.reduce((total, detail) => total + Number(detail.weighted_score || 0), 0);
    const finalScore = totalWeight ? (totalScore / totalWeight).toFixed(2) : "—";

    const rows = details.map((detail) => `
        <tr>
            <td>${escape(detail.metric)}</td>
            <td>${escape(detail.value)}</td>
            <td>${escape(detail.benchmark)}</td>
            <td>${detail.lower_is_better ? "Lower is better" : "Higher is better"}</td>
            <td>${Number(detail.score || 0).toFixed(1)}</td>
            <td>${Number(detail.weight || 0).toFixed(2)}</td>
            <td>${Number(detail.weighted_score || 0).toFixed(1)}</td>
        </tr>
    `).join("");

    const html = `
        <h2>${escape(pillar)} Performance Details</h2>
        <div class="audit-table-wrapper" style="margin-top: 15px;">
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Benchmark</th>
                        <th>Target</th>
                        <th>Score (0–100)</th>
                        <th>Weight</th>
                        <th>Weighted score</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
        <h3 style="margin-top: 15px;">Final ${escape(pillar)} Score: ${finalScore}</h3>
    `;

    document.getElementById("modalBody").innerHTML = html;
    document.getElementById("recordModal").style.display = "block";
}



