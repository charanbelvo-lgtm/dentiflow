// DentiFlow Practice Intelligence & Analytics
document.addEventListener('DOMContentLoaded', () => {
    const timeframeContainer = document.getElementById('timeframe-selector');
    let currentTimeframe = '30d';

    async function loadReports(timeframe) {
        try {
            const res = await fetch(`/api/reports?timeframe=${timeframe}`);
            if (!res.ok) throw new Error('Failed to fetch reports data');
            const data = await res.json();
            renderReports(data);
        } catch (err) {
            console.error(err);
            window.toast && window.toast('Error loading practice analytics', 'error');
        }
    }

    function renderReports(data) {
        // 1. KPI Cards
        if (data.kpis) {
            const kpiRev = document.getElementById('kpi-revenue');
            const kpiRevGrowth = document.getElementById('kpi-revenue-growth');
            const kpiPatients = document.getElementById('kpi-patients');
            const kpiPatientGrowth = document.getElementById('kpi-patient-growth');
            const kpiAvgRev = document.getElementById('kpi-avg-rev');
            const kpiNps = document.getElementById('kpi-nps');

            if (kpiRev) kpiRev.textContent = data.kpis.total_revenue;
            if (kpiRevGrowth) kpiRevGrowth.textContent = data.kpis.revenue_growth;
            if (kpiPatients) kpiPatients.textContent = data.kpis.total_patients;
            if (kpiPatientGrowth) kpiPatientGrowth.textContent = data.kpis.patient_growth;
            if (kpiAvgRev) kpiAvgRev.textContent = data.kpis.avg_revenue_per_patient;
            if (kpiNps && data.nps) kpiNps.textContent = data.nps.net_score;
        }

        // 2. Revenue Trend Bar Chart
        const barChart = document.getElementById('revenue-bar-chart');
        if (barChart && data.revenue_trend) {
            barChart.innerHTML = '';
            const values = data.revenue_trend.values || [];
            const labels = data.revenue_trend.labels || [];
            const maxVal = Math.max(...values, 1);

            values.forEach((val, idx) => {
                const heightPct = Math.max(15, Math.round((val / maxVal) * 88));
                const bar = document.createElement('div');
                bar.className = 'bar';
                bar.style.height = `${heightPct}%`;

                // Format value label (e.g. ₹4.2L or ₹45k)
                let formattedVal = `₹${Math.round(val / 1000)}k`;
                if (val >= 100000) {
                    formattedVal = `₹${(val / 100000).toFixed(1)}L`;
                }

                bar.innerHTML = `
                    <em>${formattedVal}</em>
                    <small>${labels[idx] || ''}</small>
                `;
                barChart.appendChild(bar);
            });
        }

        // 3. Clinical Care Mix
        const procContainer = document.getElementById('procedure-mix-list');
        if (procContainer && data.procedure_revenue) {
            procContainer.innerHTML = '';
            const labels = data.procedure_revenue.labels || [];
            const pcts = data.procedure_revenue.data || [];
            const colors = data.procedure_revenue.colors || [];

            labels.forEach((label, idx) => {
                const pct = pcts[idx] || 0;
                const color = colors[idx] || '#2563eb';
                const row = document.createElement('div');
                row.innerHTML = `
                    <div class="row between" style="font-size:13px;margin-bottom:4px;">
                        <b>${label}</b>
                        <span class="muted">${pct}% share</span>
                    </div>
                    <div class="progress" style="height:7px;">
                        <span style="width:${pct}%;background:${color};"></span>
                    </div>
                `;
                procContainer.appendChild(row);
            });
        }

        // 4. Doctor Share
        const docContainer = document.getElementById('doctor-share-list');
        if (docContainer && data.doctor_share) {
            docContainer.innerHTML = '';
            const labels = data.doctor_share.labels || [];
            const revs = data.doctor_share.data || [];
            const colors = data.doctor_share.colors || [];
            const totalDocRev = revs.reduce((a, b) => a + b, 0) || 1;

            labels.forEach((docName, idx) => {
                const rev = revs[idx] || 0;
                const pct = Math.round((rev / totalDocRev) * 100);
                const color = colors[idx] || '#10b981';
                const row = document.createElement('div');
                row.innerHTML = `
                    <div class="row between" style="font-size:13px;margin-bottom:4px;">
                        <div>
                            <b>${docName}</b>
                            <span class="muted" style="font-size:11px;margin-left:6px;">₹${(rev / 100000).toFixed(1)}L</span>
                        </div>
                        <span class="pill green" style="padding:1px 6px;font-size:10px;">${pct}%</span>
                    </div>
                    <div class="progress" style="height:7px;">
                        <span style="width:${pct}%;background:${color};"></span>
                    </div>
                `;
                docContainer.appendChild(row);
            });
        }
    }

    if (timeframeContainer) {
        timeframeContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-timeframe]');
            if (!btn) return;
            const tf = btn.getAttribute('data-timeframe');
            if (tf === currentTimeframe) return;

            // Update button styles
            timeframeContainer.querySelectorAll('button').forEach(b => {
                b.className = 'btn btn-ghost';
                b.style.border = '0';
            });
            btn.className = 'btn btn-primary';
            btn.style.border = '0';

            currentTimeframe = tf;
            loadReports(tf);
        });
    }

    // Initial load
    loadReports(currentTimeframe);
});
