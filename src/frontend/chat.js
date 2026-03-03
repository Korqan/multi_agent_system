document.addEventListener('DOMContentLoaded', () => {
    const industrySelect = document.getElementById('industrySelect');
    const chatForm = document.getElementById('chatForm');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatArea = document.getElementById('chatArea');

    // Auto-resize textarea
    questionInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        checkInput();
    });

    questionInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    industrySelect.addEventListener('change', checkInput);

    function checkInput() {
        if (questionInput.value.trim() && industrySelect.value) {
            sendBtn.disabled = false;
        } else {
            sendBtn.disabled = true;
        }
    }

    // Initialize
    fetchIndustries();

    async function fetchIndustries() {
        try {
            const res = await fetch('/api/v1/knowledge/industries');
            if (!res.ok) throw new Error('Failed to fetch industries');
            const industries = await res.json();

            industrySelect.innerHTML = '<option value="" disabled selected>Select an industry</option>';
            industries.forEach(ind => {
                const option = document.createElement('option');
                option.value = ind.id;
                option.textContent = ind.name;
                industrySelect.appendChild(option);
            });
            // Try to set previous selection if exists
            const savedIndustry = localStorage.getItem('last_industry_id');
            if (savedIndustry && industries.some(i => i.id == savedIndustry)) {
                industrySelect.value = savedIndustry;
            }
        } catch (err) {
            console.error(err);
            industrySelect.innerHTML = '<option value="" disabled selected>Error loading data</option>';
        }
    }

    // Submit form
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const text = questionInput.value.trim();
        const industryId = industrySelect.value;
        const industryName = industrySelect.options[industrySelect.selectedIndex].text;

        if (!text || !industryId) return;

        // Save preference
        localStorage.setItem('last_industry_id', industryId);

        // Reset input immediately
        questionInput.value = '';
        questionInput.style.height = 'auto';
        sendBtn.disabled = true;
        industrySelect.disabled = true; // Lock dropdown during query

        // Append user message
        appendMessage('user', text);

        // Show typing indicator
        const loadingId = appendMessage('ai', '...', true);

        try {
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    industry_id: parseInt(industryId),
                    question: text
                })
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: Failed to get answer`);
            }

            const data = await response.json();

            // Replaces loading with actual answer
            updateMessage(loadingId, data.answer);

        } catch (error) {
            console.error('Chat error:', error);
            updateMessage(loadingId, `Sorry, an error occurred while connecting to the knowledge base: ${error.message}`, true);
        } finally {
            industrySelect.disabled = false;
        }
    });

    function appendMessage(sender, text, isLoading = false) {
        const msgId = 'msg-' + Date.now() + Math.floor(Math.random() * 1000);

        const container = document.createElement('div');
        container.className = `message ${sender}-message`;
        if (isLoading) container.classList.add('loading-msg');
        container.id = msgId;

        let iconHTML = '';
        if (sender === 'ai') {
            iconHTML = `<div class="msg-avatar ai-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a2 2 0 0 1 2 2c-.002.321-.132.628-.358.854L10 8.5h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-8c0-1.1.9-2 2-2h1.66l-2.31-2.35A1.996 1.996 0 0 1 12 2z"></path><path d="M12 11v3"></path><path d="M10 16h4"></path></svg>
            </div>`;
        }

        container.innerHTML = `
            ${sender === 'ai' ? iconHTML : ''}
            <div class="message-content">
                ${isLoading ? `<div class="typing-indicator"><span></span><span></span><span></span></div>` : `<p>${formatText(text)}</p>`}
            </div>
            ${sender === 'user' ? `<div class="msg-avatar user-avatar"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg></div>` : ''}
        `;

        chatArea.appendChild(container);
        scrollToBottom();

        return msgId;
    }

    function updateMessage(id, text, isError = false) {
        const msgElement = document.getElementById(id);
        if (msgElement) {
            msgElement.classList.remove('loading-msg');
            const contentDiv = msgElement.querySelector('.message-content');
            contentDiv.innerHTML = `<p class="${isError ? 'error-text' : ''}">${formatText(text)}</p>`;
            scrollToBottom();
        }
    }

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    // Simple markdown formatting for bold and newlines
    function formatText(text) {
        let formatted = text.replace(/\n/g, '<br>');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return formatted;
    }
});
