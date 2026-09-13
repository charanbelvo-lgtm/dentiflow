/**
 * DentiFlow Client-Side Mock API Layer for GitHub Pages Static Demo
 * Intercepts /api/* fetch requests when running on GitHub Pages or local file preview.
 */
(function() {
    const isStaticHosting = window.location.hostname.includes('github.io') || 
                            window.location.protocol === 'file:' || 
                            !window.location.port;

    if (!isStaticHosting) return; // Use real backend when running on localhost:5000

    const originalFetch = window.fetch;

    // In-memory / localStorage mock state
    const defaultTeeth = {
        16: { tooth_number: 16, status: 'Cavity', surfaces: 'O', diagnosis: 'Deep occlusal caries', recommended_treatment: 'Composite Nano-Hybrid Restoration', estimated_cost: 2500 },
        26: { tooth_number: 26, status: 'Filling', surfaces: 'MOD', diagnosis: 'Existing composite intact', recommended_treatment: 'Routine observation', estimated_cost: 0 },
        36: { tooth_number: 36, status: 'Watch', surfaces: 'B', diagnosis: 'Incipient buccal demineralization', recommended_treatment: 'Fluoride varnish application', estimated_cost: 600 },
        46: { tooth_number: 46, status: 'Crown', surfaces: 'MOD', diagnosis: 'Post-endodontic coronal reinforcement', recommended_treatment: 'Monolithic Zirconia Crown', estimated_cost: 8500 }
    };

    window.fetch = async function(url, options = {}) {
        const urlStr = typeof url === 'string' ? url : url.url;
        const method = (options.method || 'GET').toUpperCase();

        if (!urlStr.startsWith('/api/') && !urlStr.includes('/api/')) {
            return originalFetch(url, options);
        }

        console.log(`[DentiFlow Static Demo] Intercepted ${method} ${urlStr}`);

        // Helper response creator
        function jsonResponse(data, status = 200) {
            return new Response(JSON.stringify(data), {
                status: status,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // 1. Reports API
        if (urlStr.includes('/api/reports')) {
            const urlObj = new URL(urlStr, window.location.origin);
            const tf = urlObj.searchParams.get('timeframe') || '30d';
            
            let labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
            let vals = [295000, 340000, 318000, 382000];
            let counts = [185, 210, 195, 240];

            if (tf === 'today') {
                labels = ['09:00', '11:00', '13:00', '15:00', '17:00', '19:00'];
                vals = [8500, 14200, 9500, 18500, 12000, 6800];
                counts = [2, 4, 3, 5, 3, 2];
            } else if (tf === '7d') {
                labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                vals = [42000, 38000, 52000, 49000, 64000, 58000, 48250];
                counts = [28, 25, 34, 31, 42, 39, 32];
            } else if (tf === '90d') {
                labels = ['May 2026', 'Jun 2026', 'Jul 2026', 'Aug 2026'];
                vals = [1120000, 1245000, 1310000, 1420000];
                counts = [740, 810, 860, 920];
            } else if (tf === '1y') {
                labels = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
                vals = [980000, 1020000, 1150000, 1080000, 1200000, 1180000, 1290000, 1340000, 1380000, 1410000, 1450000, 1520000];
                counts = [620, 650, 710, 680, 750, 730, 810, 840, 870, 890, 910, 960];
            }

            return jsonResponse({
                kpis: {
                    total_revenue: `₹${vals.reduce((a, b) => a + b, 0).toLocaleString('en-IN')}`,
                    revenue_growth: '+14.8%',
                    total_patients: counts.reduce((a, b) => a + b, 0),
                    patient_growth: '+9.2%',
                    avg_revenue_per_patient: `₹${Math.round(vals.reduce((a, b) => a + b, 0) / counts.reduce((a, b) => a + b, 1)).toLocaleString('en-IN')}`,
                    treatment_acceptance_rate: '84.2%',
                    no_show_rate: '3.8%'
                },
                revenue_trend: { labels: labels, values: vals },
                patient_growth: { labels: labels, values: counts },
                procedure_revenue: {
                    labels: ['Root Canal Therapy', 'Clear Aligners & Ortho', 'Zirconia Crowns & Bridges', 'Dental Implants', 'Cosmetic & Whitening', 'Preventive & Scaling'],
                    data: [32, 28, 16, 12, 8, 4],
                    colors: ['#2563EB', '#06B6D4', '#8B5CF6', '#14B8A6', '#F59E0B', '#10B981']
                },
                doctor_share: {
                    labels: ['Dr. Vikram Sharma', 'Dr. Ananya Sharma', 'Dr. Rohan Patel', 'Dr. Sneha Verma'],
                    data: [465000, 395000, 280000, 310000],
                    colors: ['#2563EB', '#06B6D4', '#14B8A6', '#8B5CF6']
                },
                nps: { promoters_pct: 82, passives_pct: 14, detractors_pct: 4, net_score: '+78' }
            });
        }

        // 2. Teeth API
        if (urlStr.includes('/teeth')) {
            const saved = JSON.parse(localStorage.getItem('dentiflow_teeth_demo') || JSON.stringify(defaultTeeth));
            if (method === 'POST') {
                const body = JSON.parse(options.body || '{}');
                saved[body.tooth_number] = body;
                localStorage.setItem('dentiflow_teeth_demo', JSON.stringify(saved));
                return jsonResponse({ status: 'success', message: 'Tooth saved', finding: body });
            }
            return jsonResponse({ findings: Object.values(saved) });
        }

        // 3. Generic Success for Modals (Appointments, Notes, Inventory, Queue)
        if (method === 'POST') {
            return jsonResponse({
                status: 'success',
                message: 'Action completed successfully in demo mode',
                data: {}
            });
        }

        // Default fallback for other GET calls
        return jsonResponse({ status: 'success', data: [] });
    };
})();
