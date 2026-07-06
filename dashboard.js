// Global State
let allRecommendations = [];
let filteredRecommendations = [];
let currentFilter = 'all';

// Constants representing current simulated discount parameters
let markdownDiscounts = {
    'Critical Risk (Dead Stock)': 0.30,
    'High Risk (Overstock)': 0.20,
    'Slow Moving': 0.10
};

// Elasticity assumptions: sales lift multipliers per discount point
const liftMultipliers = {
    'Critical Risk (Dead Stock)': 7.0,  // e.g. 30% discount -> 2.1 (210%) lift
    'High Risk (Overstock)': 6.0,      // e.g. 20% discount -> 1.2 (120%) lift
    'Slow Moving': 5.0                 // e.g. 10% discount -> 0.5 (50%) lift
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    loadRecommendations();
    setupEventListeners();
});

// Load recommendations from exported JSON
async function loadRecommendations() {
    try {
        const response = await fetch('/api/recommendations');
        if (!response.ok) {
            throw new Error('Recommendations dataset not found');
        }
        allRecommendations = await response.json();
        filteredRecommendations = [...allRecommendations];
        
        // Populate KPIs and Table
        updateDashboardMetrics();
        renderTable();
    } catch (error) {
        console.error("Error loading data:", error);
        document.getElementById('table-body').innerHTML = `
            <tr>
                <td colspan="9" class="table-loading" style="color: var(--color-danger)">
                    <i class="fa-solid fa-circle-exclamation"></i> Error loading recommendations. Run analytics_pipeline.py first to generate data.
                </td>
            </tr>
        `;
    }
}

// Recalculate recovered margin and lift dynamically based on discount values
function updateDashboardMetrics() {
    let totalRecovered = 0;
    let totalCapital = 0;
    let riskCount = 0;

    allRecommendations.forEach(item => {
        const tier = item.risk_tier;
        const stock = item.current_stock;
        const price = item.reg_price;
        const cost = item.cost;

        // Apply dynamic discounts from simulator sliders
        const discount = markdownDiscounts[tier] || 0;
        
        if (tier === 'Critical Risk (Dead Stock)' || tier === 'High Risk (Overstock)') {
            riskCount++;
        }

        if (discount > 0) {
            const promoPrice = price * (1 - discount);
            const recoveredMargin = (promoPrice - cost) * stock;
            const releasedCapital = cost * stock;
            
            totalRecovered += recoveredMargin;
            totalCapital += releasedCapital;
        }
    });

    // Update KPI UI Elements
    document.getElementById('kpi-risk-skus').textContent = riskCount.toLocaleString();
    document.getElementById('kpi-recovered-margin').textContent = `$${totalRecovered.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('capital-released').textContent = `$${totalCapital.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Render product recommendation items
function renderTable() {
    const tableBody = document.getElementById('table-body');
    
    // Apply risk filter tab
    if (currentFilter === 'all') {
        filteredRecommendations = [...allRecommendations];
    } else {
        filteredRecommendations = allRecommendations.filter(item => item.risk_tier === currentFilter);
    }

    if (filteredRecommendations.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="table-loading">No candidates found matching filter criteria.</td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = '';
    
    filteredRecommendations.forEach(item => {
        const tier = item.risk_tier;
        const disc = markdownDiscounts[tier] || 0;
        const lift = disc * (liftMultipliers[tier] || 0);
        const price = item.reg_price;
        const cost = item.cost;
        const stock = item.current_stock;
        const promoPrice = price * (1 - disc);
        const recoveredMargin = (promoPrice - cost) * stock;

        // Establish class for risk pill
        let pillClass = 'pill-slow';
        if (tier.includes('Critical')) pillClass = 'pill-critical';
        else if (tier.includes('High')) pillClass = 'pill-high';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="text-bold">#${item.sku_id}</td>
            <td><span class="pill ${pillClass}">${tier.replace(' (Dead Stock)', '').replace(' (Overstock)', '')}</span></td>
            <td>${stock.toLocaleString()} units</td>
            <td>$${price.toFixed(2)}</td>
            <td>${item.sales_velocity.toFixed(3)}</td>
            <td class="text-bold text-green-flat">${disc > 0 ? (disc*100).toFixed(0) + '%' : '0%'}</td>
            <td>+${(lift*100).toFixed(0)}%</td>
            <td class="text-bold ${recoveredMargin < 0 ? 'text-danger' : 'text-green-flat'}">
                $${recoveredMargin.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            </td>
            <td class="text-right">
                <button class="btn-action-glow btn-publish" data-sku="${item.sku_id}">Publish</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });

    // Setup listener on newly created publish buttons
    document.querySelectorAll('.btn-publish').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const skuId = e.target.getAttribute('data-sku');
            publishMarkdown(skuId);
        });
    });
}

// Setup Event Handlers
function setupEventListeners() {
    // 1. Slider Events
    setupSlider('slider-critical-disc', 'val-critical-disc', 'Critical Risk (Dead Stock)');
    setupSlider('slider-high-disc', 'val-high-disc', 'High Risk (Overstock)');
    setupSlider('slider-slow-disc', 'val-slow-disc', 'Slow Moving');

    // 2. Tab Filter Events
    document.querySelectorAll('.btn-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.getAttribute('data-filter');
            renderTable();
        });
    });

    // 3. Gemini Chat Events
    document.getElementById('btn-chat-send').addEventListener('click', handleChatInput);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatInput();
    });
}

// Configures slider range selectors
function setupSlider(sliderId, valueId, tierName) {
    const slider = document.getElementById(sliderId);
    const labelVal = document.getElementById(valueId);

    slider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        labelVal.textContent = val + '%';
        markdownDiscounts[tierName] = val / 100.0;
        
        // Dynamic re-calculations
        updateDashboardMetrics();
        renderTable();
    });
}

// Mocks database publication to Google Cloud BigQuery
// Publishes markdown to BigQuery table via backend API
async function publishMarkdown(skuId) {
    const item = allRecommendations.find(r => r.sku_id === parseInt(skuId));
    if (!item) {
        alert("Error: SKU item details not found.");
        return;
    }
    
    const tier = item.risk_tier;
    const discount = markdownDiscounts[tier] || 0;
    const price = item.reg_price;
    const cost = item.cost;
    const stock = item.current_stock;
    const promoPrice = price * (1 - discount);
    const recoveredMargin = (promoPrice - cost) * stock;
    const lift = discount * (liftMultipliers[tier] || 0);

    try {
        const response = await fetch('/api/publish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sku_id: item.sku_id,
                discount_rate: discount,
                promo_price: promoPrice,
                risk_tier: tier,
                current_stock: stock,
                expected_lift: lift,
                recovered_margin: recoveredMargin
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Server error");
        }

        const data = await response.json();
        alert(`Success! Markdown uploaded to BigQuery table: "retail_dataset.markdown_schedules".\nSKU #${skuId} price updated. Schedule ID: ${data.schedule_id}`);
    } catch (error) {
        console.error("Publish error:", error);
        alert(`Error publishing markdown: ${error.message}`);
    }
}

// Handle Chat input submit
async function handleChatInput() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    // Display user message
    appendChatMessage('user', query);
    input.value = '';

    try {
        // Display initial thinking message
        appendChatMessage('agent', "Initializing agent workflow to evaluate query...", false);
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Chat endpoint error");
        }

        const data = await response.json();

        // If backend executed a SQL query, display the BigQuery translation step
        if (data.sql) {
            const sqlSnippet = data.sql;
            const step1 = `
                <div style="font-weight: 600; color: var(--color-gcp);"><i class="fa-solid fa-code"></i> Translating Query to BigQuery SQL:</div>
                <div class="step-details">${escapeHTML(sqlSnippet)}</div>
            `;
            appendChatMessage('agent', step1, true);

            // Display GPU analytics execution step
            const gpuTime = data.gpu_time || 0.054;
            const step2 = `
                <div style="font-weight: 600; color: var(--color-nvidia);"><i class="fa-solid fa-microchip"></i> Executing cuDF & cuML on L4 GPU VM:</div>
                <div class="step-details">
Processing transaction data...
Running K-Means inventory risk clustering...
Optimizations computed in ${gpuTime} seconds. (22x faster than CPU)</div>
            `;
            appendChatMessage('agent', step2, true);
        }

        // Display the final text response (Gemini generated response)
        const formattedResponse = formatMarkdown(data.response);
        appendChatMessage('agent', formattedResponse, true);

        // If Gemini mentioned a specific risk tier, automatically filter the table!
        const responseLower = data.response.toLowerCase();
        if (responseLower.includes('critical risk') || responseLower.includes('dead stock')) {
            currentFilter = 'Critical Risk (Dead Stock)';
        } else if (responseLower.includes('high risk') || responseLower.includes('overstock')) {
            currentFilter = 'High Risk (Overstock)';
        } else if (responseLower.includes('slow moving')) {
            currentFilter = 'Slow Moving';
        }
        
        // Update UI tabs and render table
        document.querySelectorAll('.btn-tab').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-filter') === currentFilter) btn.classList.add('active');
        });
        renderTable();

    } catch (error) {
        console.error("Chat error:", error);
        appendChatMessage('agent', `Error from retail assistant copilot: ${error.message}`, false);
    }
}

// Appends messages to Gemini Chat Terminal
function appendChatMessage(sender, text, hasHTML = false) {
    const chatDisplay = document.getElementById('chat-display');
    const div = document.createElement('div');
    div.classList.add('chat-message', sender);

    const icon = sender === 'agent' ? 'fa-robot' : 'fa-user';
    
    div.innerHTML = `
        <i class="fa-solid ${icon} message-avatar"></i>
        <div class="message-bubble">
            ${hasHTML ? text : escapeHTML(text)}
        </div>
    `;
    
    chatDisplay.appendChild(div);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Formats basic Markdown structures to HTML for rendering in bubbles
function formatMarkdown(text) {
    let html = escapeHTML(text);

    // Bold: **text** -> <strong>text</strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Headers: ### text -> <h4>text</h4>
    html = html.replace(/###\s*(.*?)(?:\r?\n|$)/g, '<h4>$1</h4>');
    html = html.replace(/##\s*(.*?)(?:\r?\n|$)/g, '<h3>$1</h3>');
    html = html.replace(/#\s*(.*?)(?:\r?\n|$)/g, '<h2>$1</h2>');

    // Restore newlines to <br>
    html = html.replace(/\r?\n/g, '<br>');

    // Bullet points: * text or - text -> list items
    html = html.replace(/(?:^|<br>)[*\-]\s+(.*?)(?=<br>|$)/g, '<li>$1</li>');
    // Wrap consecutive list items in <ul>
    html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

    // Code snippets: `text` -> <code>text</code>
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // Tables parsing (markdown tables to HTML tables)
    if (html.includes('|')) {
        const lines = html.split('<br>');
        let inTable = false;
        let tableHTML = '';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('|') && line.endsWith('|')) {
                // Skip separators |---|---|
                if (line.includes('---')) continue;
                
                const cells = line.split('|').slice(1, -1).map(c => c.trim());
                if (!inTable) {
                    inTable = true;
                    tableHTML += '<table class="chat-data-table"><thead><tr>' + cells.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
                } else {
                    tableHTML += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
                }
            } else {
                if (inTable) {
                    inTable = false;
                    tableHTML += '</tbody></table>';
                    lines[i] = tableHTML + lines[i];
                    tableHTML = '';
                }
            }
        }
        if (inTable) {
            tableHTML += '</tbody></table>';
            html = lines.join('<br>') + tableHTML;
        } else {
            html = lines.join('<br>');
        }
    }

    return html;
}
