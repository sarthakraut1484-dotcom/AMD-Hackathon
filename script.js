// PRISM - Enhanced JavaScript with Image Upload & URL Scanning

document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const textAnalyzeForm = document.getElementById('analyzeForm');
    const imageForm = document.getElementById('imageForm');
    const messageInput = document.getElementById('messageInput');
    const imageInput = document.getElementById('imageInput');
    const imageUploadArea = document.getElementById('imageUploadArea');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const analyzeImageBtn = document.getElementById('analyzeImageBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');

    let selectedImage = null;

    // Image upload area click
    if (imageUploadArea) {
        imageUploadArea.addEventListener('click', () => {
            imageInput.click();
        });

        // Drag and drop handlers
        imageUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            imageUploadArea.style.borderColor = '#06b6d4';
            imageUploadArea.style.background = 'rgba(6, 182, 212, 0.1)';
        });

        imageUploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            imageUploadArea.style.borderColor = 'rgba(100, 200, 255, 0.3)';
            imageUploadArea.style.background = '';
        });

        imageUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            imageUploadArea.style.borderColor = 'rgba(100, 200, 255, 0.3)';
            imageUploadArea.style.background = '';

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageFile(files[0]);
            }
        });
    }

    // Image input change
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleImageFile(e.target.files[0]);
            }
        });
    }

    function handleImageFile(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file');
            return;
        }

        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            alert('File size must be less than 16MB');
            return;
        }

        selectedImage = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
            uploadPlaceholder.style.display = 'none';
            analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // Text form submission
    if (textAnalyzeForm) {
        textAnalyzeForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const message = messageInput.value.trim();

            if (!message) {
                alert('Please enter a message to analyze');
                return;
            }

            await analyzeText(message);
        });
    }

    // Image form submission
    if (imageForm) {
        imageForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            if (!selectedImage) {
                alert('Please select an image first');
                return;
            }

            await analyzeImage(selectedImage);
        });
    }

    async function analyzeText(text) {
        loadingSpinner.style.display = 'block';
        resultsContainer.style.display = 'none';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Analysis failed');
            }

            displayResults(data);
            playPingSound();
            if (data && data.prediction) {
                let currentLanguage = data.language;
                if (data.language_code && data.language_code !== 'unknown') {
                    try {
                        const names = new Intl.DisplayNames(['en'], { type: 'language' });
                        const formattedName = names.of(data.language_code);
                        currentLanguage = formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
                    } catch (e) { }
                }
                addLocalHistory(currentLanguage, data.prediction, false);
            }

        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    async function analyzeImage(imageFile) {
        loadingSpinner.style.display = 'block';
        resultsContainer.style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('image', imageFile);

            const response = await fetch('/analyze-image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                let errorMsg = data.error || 'Image analysis failed';
                if (data.installation_guide) {
                    errorMsg += '\n\n' + data.installation_guide;
                }
                throw new Error(errorMsg);
            }

            // Show extracted text in a special section
            if (data.extracted_text) {
                showExtractedText(data.extracted_text, data.ocr_metadata);
            }

            displayResults(data);
            playPingSound();
            if (data && data.prediction) {
                let currentLanguage = data.language || 'Various';
                if (data.language_code && data.language_code !== 'unknown') {
                    try {
                        const names = new Intl.DisplayNames(['en'], { type: 'language' });
                        const formattedName = names.of(data.language_code);
                        currentLanguage = formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
                    } catch (e) { }
                }
                addLocalHistory(currentLanguage, data.prediction, true);
            }

        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    // --- Added Interactive Features ---
    function playPingSound() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const audioCtx = new AudioContext();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(1200, audioCtx.currentTime + 0.1);
            gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, audioCtx.currentTime + 0.05);
            gainNode.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.3);
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.3);
        } catch (e) { console.log("Audio not supported"); }
    }

    async function fetchLiveRecentScans() {
        const historyContainer = document.getElementById('localScanHistory');
        if (!historyContainer) return;

        try {
            const response = await fetch('/api/recent-reports?limit=5');
            const reports = await response.json();

            if (!reports || reports.length === 0) {
                historyContainer.innerHTML = '<p class="text-custom-subtle small opacity-75">No recent scans found.</p>';
                return;
            }

            let html = '';
            reports.forEach(report => {
                const isSafe = report.risk_level.toLowerCase() === 'safe';
                let iconClass = isSafe ? 'bi-shield-check text-success' :
                    (report.risk_level.toLowerCase() === 'suspicious' ? 'bi-shield-exclamation text-warning' : 'bi-shield-exclamation text-danger badge-pulse');

                let displayLanguage = report.language || 'Unknown';
                if (report.language_code && report.language_code !== 'unknown') {
                    try {
                        const names = new Intl.DisplayNames(['en'], { type: 'language' });
                        const formattedName = names.of(report.language_code);
                        displayLanguage = formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
                    } catch (e) { }
                }

                const date = new Date(report.timestamp);
                const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const typeStr = report.source === 'image' ? '📸' : '📝';

                html += `
                    <div class="list-group-item bg-transparent border rounded p-2 text-custom-subtle small d-flex justify-content-between align-items-center hover-lift mt-2">
                        <span><i class="bi ${iconClass} me-2"></i> ${typeStr} ${displayLanguage} | ${report.risk_level}</span>
                        <span class="opacity-75">${timeStr}</span>
                    </div>
                `;
            });

            historyContainer.innerHTML = html;
        } catch (e) {
            console.error("Failed to fetch live scans:", e);
        }
    }

    if (document.getElementById('localScanHistory')) {
        fetchLiveRecentScans();
        setInterval(fetchLiveRecentScans, 10000);
    }

    function addLocalHistory(language, riskLevel, isImage) {
        // Trigger an immediate live update fetch to pull the newly added scan from the DB
        setTimeout(fetchLiveRecentScans, 500);
    }

    function showExtractedText(text, metadata) {
        // Create or update extracted text section
        let extractedSection = document.getElementById('extractedTextSection');

        if (!extractedSection) {
            extractedSection = document.createElement('div');
            extractedSection.id = 'extractedTextSection';
            extractedSection.className = 'card glass-card mb-4';
            resultsContainer.insertBefore(extractedSection, resultsContainer.firstChild);
        }

        extractedSection.innerHTML = `
            <div class="card-body p-4">
                <h3 class="h5 mb-3">📄 Extracted Text from Image</h3>
                <div class="result-box mb-3">
                    <p class="mb-0" style="white-space: pre-wrap;">${escapeHtml(text)}</p>
                </div>
                ${metadata ? `
                    <div class="small text-custom-subtle">
                        <span class="me-3">📊 Words: ${metadata.words_detected}</span>
                        <span class="me-3">✅ Confidence: ${metadata.average_confidence}%</span>
                        <span>🌐 Languages: ${metadata.languages_checked.slice(0, 3).join(', ')}</span>
                    </div>
                ` : ''}
            </div>
        `;
        extractedSection.style.display = 'block';
    }

    function displayResults(data) {
        // Risk Level
        const riskLevel = document.getElementById('riskLevel');
        const prediction = data.prediction.toUpperCase();
        riskLevel.textContent = `🎯 ${prediction}`;

        // Apply color class
        riskLevel.className = '';
        if (prediction === 'SAFE') {
            riskLevel.classList.add('risk-safe');
        } else if (prediction === 'SUSPICIOUS') {
            riskLevel.classList.add('risk-suspicious');
        } else {
            riskLevel.classList.add('risk-scam');
        }

        // Detected Language
        let displayName = data.language;
        if (data.language_code && data.language_code !== 'unknown') {
            try {
                const names = new Intl.DisplayNames(['en'], { type: 'language' });
                // Make sure the first letter is capitalized for consistency
                const formattedName = names.of(data.language_code);
                displayName = formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
            } catch (e) {
                console.warn('Could not format language code:', e);
            }
        }
        document.getElementById('detectedLanguage').textContent = displayName;

        // Risk Score
        const riskScore = Math.min(Math.max(data.risk_score, 0), 100);
        const riskScoreCircle = document.getElementById('riskScoreCircle');
        const riskScoreValue = document.getElementById('riskScoreValue');

        if (riskScoreCircle) {
            riskScoreCircle.setAttribute('stroke-dasharray', `${riskScore}, 100`);

            // Color the progress circle based on risk
            if (riskScore >= 70) {
                riskScoreCircle.setAttribute('stroke', '#ef4444');
            } else if (riskScore >= 40) {
                riskScoreCircle.setAttribute('stroke', '#f59e0b');
            } else {
                riskScoreCircle.setAttribute('stroke', '#10b981');
            }
        }

        if (riskScoreValue) {
            riskScoreValue.textContent = riskScore + '%';
        }

        // Combined Confidence Chart
        const scamConf = data.confidence.scam;
        const safeConf = data.confidence.safe;

        const donut = document.getElementById('confidenceDonut');
        if (donut) {
            donut.style.background = `conic-gradient(#ef4444 0% ${scamConf}%, #10b981 ${scamConf}% 100%)`;
        }

        const scamConfVal = document.getElementById('scamConfidenceValue');
        if (scamConfVal) scamConfVal.textContent = scamConf + '%';

        const safeConfVal = document.getElementById('safeConfidenceValue');
        if (safeConfVal) safeConfVal.textContent = safeConf + '%';

        // Message Statistics
        document.getElementById('statCharacters').textContent = data.stats.characters;
        document.getElementById('statWords').textContent = data.stats.words;
        document.getElementById('statUrls').textContent = data.stats.urls;
        document.getElementById('statPhones').textContent = data.stats.phones;

        // Explanation
        document.getElementById('explanationText').textContent = data.explanation;

        // URL Scan Results (if available)
        displayUrlScans(data.url_scans);

        // Detected Indicators
        const indicatorsSection = document.getElementById('indicatorsSection');
        let hasIndicators = false;

        // Keywords
        if (data.suspicious_keywords && data.suspicious_keywords.length > 0) {
            hasIndicators = true;
            const keywordsSection = document.getElementById('keywordsSection');
            const keywordsList = document.getElementById('keywordsList');

            keywordsList.innerHTML = '';
            data.suspicious_keywords.slice(0, 10).forEach(keyword => {
                const badge = document.createElement('span');
                badge.className = 'badge-keyword';
                badge.textContent = keyword;
                keywordsList.appendChild(badge);
            });

            keywordsSection.style.display = 'block';
        } else {
            document.getElementById('keywordsSection').style.display = 'none';
        }

        // URLs
        if (data.urls_found && data.urls_found.length > 0) {
            hasIndicators = true;
            const urlsSection = document.getElementById('urlsSection');
            const urlsList = document.getElementById('urlsList');

            urlsList.innerHTML = '';
            data.urls_found.forEach(url => {
                const li = document.createElement('li');
                li.innerHTML = `<code class="text-primary">${escapeHtml(url)}</code>`;
                urlsList.appendChild(li);
            });

            urlsSection.style.display = 'block';
        } else {
            document.getElementById('urlsSection').style.display = 'none';
        }

        // Phone Numbers
        if (data.phone_numbers_found && data.phone_numbers_found.length > 0) {
            hasIndicators = true;
            const phonesSection = document.getElementById('phonesSection');
            const phonesList = document.getElementById('phonesList');

            phonesList.innerHTML = '';
            data.phone_numbers_found.forEach(phone => {
                const li = document.createElement('li');
                li.innerHTML = `<code class="text-primary">${escapeHtml(phone)}</code>`;
                phonesList.appendChild(li);
            });

            phonesSection.style.display = 'block';
        } else {
            document.getElementById('phonesSection').style.display = 'none';
        }

        // Show/hide indicators section
        indicatorsSection.style.display = hasIndicators ? 'block' : 'none';

        // Risk Indicators
        const indicators = data.indicators;
        setIndicator('indUrgency', indicators.has_urgency);
        setIndicator('indFinancial', indicators.has_financial_terms);
        setIndicator('indAction', indicators.has_action_required);
        setIndicator('indThreats', indicators.has_threats);
        setIndicator('indPersonal', indicators.requests_personal_info);
        setIndicator('indLinks', indicators.contains_urls);

        // Show results with animation
        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function displayUrlScans(urlScans) {
        if (!urlScans || urlScans.length === 0) {
            return;
        }

        // Create or update URL scan section
        let urlScanSection = document.getElementById('urlScanSection');

        if (!urlScanSection) {
            urlScanSection = document.createElement('div');
            urlScanSection.id = 'urlScanSection';
            urlScanSection.className = 'card glass-card mb-4';

            // Insert after indicators section
            const indicatorsSection = document.getElementById('indicatorsSection');
            indicatorsSection.parentNode.insertBefore(urlScanSection, indicatorsSection.nextSibling);
        }

        let html = `
            <div class="card-body p-4">
                <h3 class="h5 mb-4">🔗 URL Security Analysis</h3>
        `;

        urlScans.forEach((scan, index) => {
            const riskColor = scan.risk_level === 'HIGH' ? 'danger' : scan.risk_level === 'MEDIUM' ? 'warning' : 'success';

            html += `
                <div class="result-box mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <code class="text-primary">${escapeHtml(scan.url)}</code>
                        <span class="badge bg-${riskColor}">${scan.risk_level} RISK</span>
                    </div>
                    <div class="progress mb-2" style="height: 20px;">
                        <div class="progress-bar bg-${riskColor}" style="width: ${scan.risk_score}%">
                            ${scan.risk_score}%
                        </div>
                    </div>
                    ${scan.warnings && scan.warnings.length > 0 ? `
                        <div class="small text-custom-subtle">
                            <strong>⚠️ Warnings:</strong>
                            <ul class="mb-0 mt-1">
                                ${scan.warnings.slice(0, 3).map(w => `<li>${escapeHtml(w)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += '</div>';
        urlScanSection.innerHTML = html;
        urlScanSection.style.display = 'block';
    }

    function setIndicator(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value ? 'Yes' : 'No';
            element.className = 'indicator-value ' + (value ? 'indicator-yes' : 'indicator-no');
        }
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Character Counter
    if (messageInput) {
        const charCount = document.getElementById('charCount');
        messageInput.addEventListener('input', function () {
            if (charCount) {
                charCount.textContent = this.value.length + ' characters';
            }
        });
    }

    // Dark Mode Toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    const themeIcon = document.getElementById('themeIcon');

    // Check saved theme initially
    const savedTheme = localStorage.getItem('prism-theme');
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        if (themeIcon) {
            themeIcon.className = 'bi bi-sun-fill text-warning';
        }
    }

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme');
            let newTheme = 'dark';

            if (currentTheme === 'dark') {
                newTheme = 'light';
                document.body.removeAttribute('data-theme');
                if (themeIcon) themeIcon.className = 'bi bi-moon-fill';
            } else {
                document.body.setAttribute('data-theme', 'dark');
                if (themeIcon) themeIcon.className = 'bi bi-sun-fill text-warning';
            }
            localStorage.setItem('prism-theme', newTheme);
        });
    }

    // Sticky Navbar Shrink
    window.addEventListener('scroll', function () {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 30) {
                navbar.classList.add('navbar-shrink');
            } else {
                navbar.classList.remove('navbar-shrink');
            }
        }
    });

});
