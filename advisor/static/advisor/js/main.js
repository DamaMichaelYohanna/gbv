/**
 * Nasarawa State University, Keffi (NSUK)
 * GBV Advisory Portal & Confidential Chat Application
 * Client-Side Controller (Landing Page & Chat Workspace)
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- UTILITIES ---

    // Get CSRF Token from Cookie
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Log stats anonymously
    async function logStat(action) {
        try {
            await fetch('/api/log-stat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ action: action })
            });
        } catch (e) {
            console.error('Stat logging error:', e);
        }
    }

    // --- QUICK EXIT FUNCTIONALITY (ESC KEY & BUTTON) ---
    function executeQuickExit() {
        // Log action anonymously
        logStat('quick_exit');

        // Wipe local session chat & planner data
        sessionStorage.removeItem('gbv_chat_messages');
        localStorage.removeItem('gbv_safety_plan_checklist');
        localStorage.removeItem('gbv_safety_plan_custom');

        // Immediately redirect to a neutral, unsuspicious website (Google)
        window.location.replace('https://www.google.com');
    }

    // Bind all quick exit buttons
    document.querySelectorAll('.btn-quick-exit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            executeQuickExit();
        });
    });

    // ESC key triggers Quick Exit on any page
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            executeQuickExit();
        }
    });

    // --- LANDING PAGE: DIRECTORY SEARCH ---
    const homeSearchBtn = document.getElementById('home-search-btn');
    const homeStateSelect = document.getElementById('home-state-select');
    const homeCategorySelect = document.getElementById('home-category-select');
    const homeDirectoryResults = document.getElementById('home-directory-results');

    if (homeSearchBtn && homeDirectoryResults) {
        homeSearchBtn.addEventListener('click', async () => {
            const state = homeStateSelect ? homeStateSelect.value : '';
            const category = homeCategorySelect ? homeCategorySelect.value : '';

            let queryParams = [];
            if (state) queryParams.push(`state=${encodeURIComponent(state)}`);
            if (category) queryParams.push(`category=${encodeURIComponent(category)}`);

            const url = `/api/directory/${queryParams.length > 0 ? '?' + queryParams.join('&') : ''}`;

            homeDirectoryResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 32px; color: var(--text-muted); font-size: 1rem;"><div class="typing-indicator" style="justify-content: center;"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>Searching campus & state services...</div>';

            try {
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    renderDirectoryCards(data.results, homeDirectoryResults);
                } else {
                    homeDirectoryResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 24px; color: var(--danger-red);">Unable to retrieve organizations. Please try again later.</div>';
                }
            } catch (error) {
                console.error('Home directory search error:', error);
                homeDirectoryResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 24px; color: var(--danger-red);">Network error. Please verify your connection.</div>';
            }
        });
    }

    // Helper: Render Organization Cards into a Container
    function renderDirectoryCards(orgs, container) {
        container.innerHTML = '';

        if (!orgs || orgs.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 36px; background: #ffffff; border: 1px dashed var(--border-light); border-radius: 12px;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">⚠️</div>
                    <div style="font-weight: 700; color: var(--text-main); margin-bottom: 6px;">No support services matched your filter.</div>
                    <div style="color: var(--text-muted); font-size: 0.875rem;">Try selecting "All States" or another category, or contact the NSUK Security Dispatch at 08023456789.</div>
                </div>
            `;
            return;
        }

        orgs.forEach(org => {
            const card = document.createElement('div');
            card.classList.add('org-card');

            let contactsHtml = '';
            if (org.phone_number) {
                contactsHtml += `<div class="org-contact-item"><span>📞 Phone:</span> <a href="tel:${org.phone_number}">${org.phone_number}</a></div>`;
            }
            if (org.alt_phone_number) {
                contactsHtml += `<div class="org-contact-item"><span>📞 Alt:</span> <a href="tel:${org.alt_phone_number}">${org.alt_phone_number}</a></div>`;
            }
            if (org.email) {
                contactsHtml += `<div class="org-contact-item"><span>✉️ Email:</span> <a href="mailto:${org.email}">${org.email}</a></div>`;
            }
            if (org.website) {
                contactsHtml += `<div class="org-contact-item"><span>🌐 Website:</span> <a href="${org.website}" target="_blank" rel="noopener">Visit Web Portal</a></div>`;
            }

            card.innerHTML = `
                <div class="org-header">
                    <h3 class="org-name">${org.name}</h3>
                    <span class="org-category">${org.category || org.category_code}</span>
                </div>
                <p class="org-detail">${org.description || ''}</p>
                <p class="org-detail" style="font-size: 0.8rem;">📍 <strong>Location:</strong> ${org.address || org.state}</p>
                <div class="org-contacts-list">
                    ${contactsHtml}
                </div>
            `;
            container.appendChild(card);
        });
    }

    // --- CHAT PAGE WORKSPACE LOGIC ---
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Only execute if on Chat Page
    if (chatHistory && chatInput && sendBtn) {
        let conversationHistory = [];

        // Format bot text with bold and breaks
        function formatBotMessage(text) {
            if (!text) return '';
            let formatted = text.replace(/\n/g, '<br>');
            formatted = formatted.replace(/(?:^|<br>)\s*•\s*([^<]+)/g, '<br>• $1');
            formatted = formatted.replace(/(?:^|<br>)\s*(\d+\.)\s*([^<]+)/g, '<br><strong>$1</strong> $2');
            return formatted;
        }

        // Add message to chat history UI
        function appendMessage(sender, text, isHtml = false) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('message-wrapper', sender);

            const bubble = document.createElement('div');
            bubble.classList.add('message-bubble');

            if (isHtml) {
                bubble.innerHTML = text;
            } else {
                bubble.textContent = text;
            }

            const meta = document.createElement('div');
            meta.classList.add('message-meta');
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const name = sender === 'bot' ? 'Endy (Advisor)' : 'You (Anonymous)';
            meta.innerHTML = `<span>${name}</span><span>${time}</span>`;

            wrapper.appendChild(bubble);
            wrapper.appendChild(meta);
            chatHistory.appendChild(wrapper);

            chatHistory.scrollTop = chatHistory.scrollHeight;
            setTimeout(() => {
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }, 60);

            // Store in session storage
            conversationHistory.push({ sender, text, isHtml });
            sessionStorage.setItem('gbv_chat_messages', JSON.stringify(conversationHistory));
        }

        function showTypingIndicator() {
            const wrapper = document.createElement('div');
            wrapper.classList.add('message-wrapper', 'bot', 'typing-wrapper');

            const indicator = document.createElement('div');
            indicator.classList.add('message-bubble', 'typing-indicator');
            indicator.innerHTML = `
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            `;

            wrapper.appendChild(indicator);
            chatHistory.appendChild(wrapper);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        function removeTypingIndicator() {
            const indicator = document.querySelector('.typing-wrapper');
            if (indicator) {
                indicator.remove();
            }
        }

        // Send Message Handler
        async function sendMessage() {
            const messageText = chatInput.value.trim();
            if (!messageText) return;

            chatInput.value = '';
            appendMessage('user', messageText);

            showTypingIndicator();

            try {
                const response = await fetch('/api/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({ message: messageText })
                });

                removeTypingIndicator();

                if (response.ok) {
                    const data = await response.json();
                    let botReply = formatBotMessage(data.response);

                    // Add action buttons if suggested
                    if (data.suggested_action && data.suggested_action !== 'none') {
                        let btnLabel = data.suggested_action === 'safety_plan' ? '📋 Open Safety Planner' : '🔎 Search Support Directory';
                        botReply += `<br><button class="btn-cta-chat" style="margin-top: 12px; font-size: 0.8rem; padding: 6px 14px;" onclick="handleBotAction('${data.suggested_action}')">${btnLabel}</button>`;
                    }

                    appendMessage('bot', botReply, true);
                } else {
                    appendMessage('bot', 'I encountered an error communicating with the server. Please try again.');
                }
            } catch (error) {
                removeTypingIndicator();
                appendMessage('bot', 'Network error. Please verify your connection.');
                console.error('Chat API Error:', error);
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Global helper for suggestion chips
        window.sendSuggestedMessage = function(promptText) {
            if (chatInput) {
                chatInput.value = promptText;
                sendMessage();
            }
        };

        // Global helper for bot action triggers
        window.handleBotAction = function(actionType) {
            if (actionType === 'safety_plan') {
                openTab('tab-planner');
            } else if (actionType === 'directory_search') {
                openTab('tab-directory');
            }
        };

        // Load Session Chat History or Welcome Message
        function loadChatSession() {
            const saved = sessionStorage.getItem('gbv_chat_messages');
            if (saved) {
                conversationHistory = JSON.parse(saved);
                conversationHistory.forEach(msg => {
                    appendMessage(msg.sender, msg.text, msg.isHtml);
                });
            } else {
                // Initial welcoming greeting with NSUK branded suggestion chips
                appendMessage(
                    'bot',
                    'Hello. I am <strong>Endy</strong>, your confidential advisory assistant for Nasarawa State University, Keffi (NSUK). I am here to provide compassionate, safe, and completely anonymous guidance. You can ask me anything about gender-based violence, sexual harassment, safety planning, or finding help.<div class="suggestion-chips"><button class="chip-btn" onclick="sendSuggestedMessage(\'I am in immediate danger\')">🚨 Emergency Help</button><button class="chip-btn" onclick="sendSuggestedMessage(\'Request information about types of GBV\')">📖 Types of GBV</button><button class="chip-btn" onclick="sendSuggestedMessage(\'I am feeling so distressed and overwhelmed\')">💜 Emotional Support</button><button class="chip-btn" onclick="sendSuggestedMessage(\'Request safety guidance\')">🛡️ Safety Guidance</button><button class="chip-btn" onclick="sendSuggestedMessage(\'Request contact information for support services\')">📞 Support Referrals</button><button class="chip-btn" onclick="sendSuggestedMessage(\'How do I make a safety plan?\')">📝 Make a Safety Plan</button></div>',
                    true
                );
            }
        }

        loadChatSession();
    }

    // --- TAB SWITCHER LOGIC ---
    function openTab(tabId) {
        tabButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        const targetPane = document.getElementById(tabId);

        if (targetBtn) targetBtn.classList.add('active');
        if (targetPane) targetPane.classList.add('active');

        logStat(`viewed_tab_${tabId}`);
    }

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            openTab(targetTab);
        });
    });

    // Check URL parameters to auto-open specific tab (e.g. ?tab=tab-planner)
    const urlParams = new URLSearchParams(window.location.search);
    const requestedTab = urlParams.get('tab');
    if (requestedTab && document.getElementById(requestedTab)) {
        openTab(requestedTab);
    }

    // --- CHAT PAGE: DIRECTORY SEARCH ---
    const searchOrgsBtn = document.getElementById('search-orgs-btn');
    const stateSelect = document.getElementById('state-select');
    const categorySelect = document.getElementById('category-select');
    const directoryResults = document.getElementById('directory-results');

    if (searchOrgsBtn && directoryResults) {
        searchOrgsBtn.addEventListener('click', async () => {
            const state = stateSelect ? stateSelect.value : '';
            const category = categorySelect ? categorySelect.value : '';

            let queryParams = [];
            if (state) queryParams.push(`state=${encodeURIComponent(state)}`);
            if (category) queryParams.push(`category=${encodeURIComponent(category)}`);

            const url = `/api/directory/${queryParams.length > 0 ? '?' + queryParams.join('&') : ''}`;

            directoryResults.innerHTML = '<div style="text-align: center; padding: 24px;"><div class="typing-indicator" style="justify-content: center;"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>Searching directory...</div>';

            try {
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    renderDirectoryCards(data.results, directoryResults);
                } else {
                    directoryResults.innerHTML = '<div style="text-align: center; padding: 18px; color: var(--danger-red);">Failed to retrieve support services.</div>';
                }
            } catch (error) {
                directoryResults.innerHTML = '<div style="text-align: center; padding: 18px; color: var(--danger-red);">Network error. Please check your connection.</div>';
                console.error('Directory search error:', error);
            }
        });
    }

    // --- SAFETY PLANNER LOGIC ---
    const checklistInputs = document.querySelectorAll('.planner-checklist input[type="checkbox"]');
    const progressBar = document.getElementById('planner-progress-bar');
    const progressText = document.getElementById('planner-progress-text');
    const downloadPlanBtn = document.getElementById('download-plan-btn');
    const clearPlanBtn = document.getElementById('clear-plan-btn');

    function updatePlannerProgress() {
        if (!checklistInputs || checklistInputs.length === 0) return;
        const total = checklistInputs.length;
        let checked = 0;
        checklistInputs.forEach(input => {
            if (input.checked) checked++;
        });

        const percent = Math.round((checked / total) * 100);
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressText) progressText.textContent = `${percent}% Complete`;
    }

    function saveChecklistState() {
        const checkedIds = [];
        checklistInputs.forEach(input => {
            if (input.checked) checkedIds.push(input.id);
        });
        localStorage.setItem('gbv_safety_plan_checklist', JSON.stringify(checkedIds));
        updatePlannerProgress();
    }

    function loadChecklistState() {
        const saved = localStorage.getItem('gbv_safety_plan_checklist');
        if (saved) {
            try {
                const checkedIds = JSON.parse(saved);
                checklistInputs.forEach(input => {
                    input.checked = checkedIds.includes(input.id);
                });
            } catch (e) {
                console.error('Error loading checklist:', e);
            }
        }
        updatePlannerProgress();
    }

    if (checklistInputs.length > 0) {
        checklistInputs.forEach(input => {
            input.addEventListener('change', saveChecklistState);
        });
        loadChecklistState();
    }

    // Print / Download Plan
    if (downloadPlanBtn) {
        downloadPlanBtn.addEventListener('click', () => {
            logStat('downloaded_safety_plan');
            window.print();
        });
    }

    // Clear Checklist
    if (clearPlanBtn) {
        clearPlanBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear your safety plan? This deletes all checkmarks from your private local storage.')) {
                localStorage.removeItem('gbv_safety_plan_checklist');
                checklistInputs.forEach(input => {
                    input.checked = false;
                });
                updatePlannerProgress();
                logStat('cleared_safety_plan');
            }
        });
    }
});
