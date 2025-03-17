const API_URL = 'http://localhost:8000';

async function analyzeVideo() {
    const videoId = document.getElementById('videoId').value;
    if (!videoId) {
        alert('Please enter a YouTube Video ID');
        return;
    }

    showLoading(true);
    clearPreviousResults();

    try {
        // Get sentiment stats first
        const sentimentStats = await fetch(`${API_URL}/sentiment-stats/${videoId}`);
        const sentimentData = await handleResponse(sentimentStats);
        
        // Get analysis
        const analysis = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ video_id: videoId })
        });
        const data = await handleResponse(analysis);
        
        updateDashboard(data);
        updateSentimentChart(sentimentData.sentiment_distribution);  // Re-add this line
        removePlaceholders();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'An error occurred');
    }
    return response.json();
}

function showError(message) {
    alert(`Analysis failed: ${message}. Please try again.`);
}

function clearPreviousResults() {
    document.getElementById('totalComments').textContent = '-';
    document.getElementById('issuesContainer').innerHTML = '';
    document.getElementById('recommendationsContainer').innerHTML = '';
    const chartCanvas = document.getElementById('sentimentChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
    }
}

function updateDashboard(data) {
    animateNumber('totalComments', 0, data.overview.total_comments);

    // Update major issues
    const issuesContainer = document.getElementById('issuesContainer');
    if (data.major_issues.issues && data.major_issues.issues.length > 0) {
        issuesContainer.innerHTML = data.major_issues.issues.map((issue, index) => `
            <div class="issue-card" style="animation: slideIn ${0.2 + index * 0.1}s ease-out">
                <div class="issue-header">
                    <span class="issue-number">${index + 1}</span>
                    <h3 class="issue-title">Problem & Solution #${index + 1}</h3>
                </div>
                <div class="issue-content">
                    <div class="problem-box">
                        <h4>🚨 Problem:</h4>
                        <p>${issue.problem || 'No problem specified'}</p>
                    </div>
                    <div class="solution-box">
                        <h4>✅ Solution:</h4>
                        <p>${issue.solution || 'No solution specified'}</p>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        issuesContainer.innerHTML = '<div class="no-data">No major issues found</div>';
    }

    // Update recommendations with better formatting
    const recsContainer = document.getElementById('recommendationsContainer');
    if (data.recommendations?.actions?.length > 0) {
        recsContainer.innerHTML = `
            <div class="recommendations-grid">
                ${data.recommendations.actions.map((rec, index) => `
                    <div class="recommendation-item" style="animation: slideIn ${0.2 + index * 0.1}s ease-out">
                        <div class="rec-header">
                            <span class="rec-number">${index + 1}</span>
                        </div>
                        <div class="rec-content">
                            <p>${rec.text || 'No recommendation specified'}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        recsContainer.innerHTML = '<div class="no-data">No recommendations available</div>';
    }
}

function formatIssue(text) {
    return text
        .replace(/^Problem:?\s*/i, '')
        .replace(/^\d+\.\s*/, '')
        .trim();
}

function formatSolution(text) {
    return text
        .replace(/^Solution:?\s*/i, '')
        .replace(/^\d+\.\s*/, '')
        .replace(/^[-•]\s*/, '')
        .trim();
}

function updateSentimentChart(distribution) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    // New chart configuration
    const chartConfig = {
        colors: {
            '1': '#FF4136',
            '2': '#FF851B', 
            '3': '#FFDC00',
            '4': '#2ECC40',
            '5': '#0074D9'
        },
        labels: {
            '1': '⭐ Very Poor',
            '2': '⭐⭐ Poor',
            '3': '⭐⭐⭐ Average',
            '4': '⭐⭐⭐⭐ Good',
            '5': '⭐⭐⭐⭐⭐ Excellent'
        }
    };

    // Properly destroy existing chart
    if (window.sentimentChart instanceof Chart) {
        window.sentimentChart.destroy();
    }

    // Create new chart
    window.sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(distribution).map(key => chartConfig.labels[key] || `Rating ${key}`),
            datasets: [{
                data: Object.values(distribution),
                backgroundColor: Object.keys(distribution).map(key => chartConfig.colors[key] || '#999999'),
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: 20
            },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12,
                            family: 'Inter'
                        },
                        generateLabels: (chart) => {
                            const { data } = chart;
                            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                            return data.labels.map((label, i) => ({
                                text: `${label} - ${data.datasets[0].data[i]} (${((data.datasets[0].data[i]/total)*100).toFixed(1)}%)`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: '#fff',
                                lineWidth: 2,
                                hidden: false
                            }));
                        }
                    }
                }
            }
        }
    });
}

function animateNumber(elementId, start, end) {
    const duration = 1000;
    const element = document.getElementById(elementId);
    const increment = (end - start) / (duration / 16);
    let current = start;

    const animate = () => {
        current += increment;
        element.textContent = Math.round(current);
        
        if (current < end) {
            requestAnimationFrame(animate);
        } else {
            element.textContent = end;
        }
    };
    
    animate();
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

// Add keypress event listener for enter key
document.getElementById('videoId').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        analyzeVideo();
    }
});

function startAnalysis() {
    const videoId = document.getElementById('welcomeVideoId').value;
    if (!videoId) {
        alert('Please enter a YouTube Video ID');
        return;
    }
    
    // Hide welcome screen
    document.getElementById('welcome-screen').style.display = 'none';
    // Show main interface
    document.querySelector('nav').style.display = 'block';
    document.querySelector('main').style.display = 'block';
    
    // Copy ID to main search
    document.getElementById('videoId').value = videoId;
    // Start analysis
    analyzeVideo();
}

// Add enter key listener for welcome screen
document.getElementById('welcomeVideoId').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        startAnalysis();
    }
});

function removePlaceholders() {
    document.querySelectorAll('.placeholder').forEach(el => {
        el.classList.remove('placeholder');
    });
}

// Add these styles to your existing CSS
const styles = `
    .timeline-badge {
        padding: 4px 12px;
        border-radius: 12px;
        color: white;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .impact-box {
        margin-top: 1rem;
        padding: 0.8rem;
        background: rgba(0, 123, 255, 0.05);
        border-radius: 8px;
        border-left: 3px solid #2196F3;
    }
    
    .impact-box h5 {
        margin: 0 0 0.5rem 0;
        color: #2196F3;
        font-size: 0.9rem;
    }
    
    .action-text {
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
`;

// Inject the styles
const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);
