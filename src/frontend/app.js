document.addEventListener('DOMContentLoaded', () => {
    const industrySelect = document.getElementById('industrySelect');
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');

    // Batch elements
    const fileListContainer = document.getElementById('fileListContainer');
    const fileList = document.getElementById('fileList');
    const fileCount = document.getElementById('fileCount');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const uploadTitle = dropZone.querySelector('.upload-title');
    const uploadHint = dropZone.querySelector('.upload-hint');

    const statusMessage = document.getElementById('statusMessage');
    const statusTitle = document.getElementById('statusTitle');
    const statusDesc = document.getElementById('statusDesc');
    const closeStatus = document.querySelector('.close-status');

    let selectedFiles = [];

    // 1. Fetch Industries on Load
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
        } catch (err) {
            console.error(err);
            showStatus('Error Loading Industries', 'Could not load industry list. Please refresh.', 'error');
            industrySelect.innerHTML = '<option value="" disabled selected>Error loading data</option>';
        }
    }

    // 2. Drag and Drop Handling
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', function () {
        if (this.files && this.files.length > 0) {
            handleFiles(Array.from(this.files));
        }
        // Reset input so selecting the same files again works if they were removed from the list
        this.value = '';
    });

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFiles(Array.from(files));
        }
    }

    function handleFiles(files) {
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const validExts = ['.pdf', '.doc', '.docx'];
        let invalidFound = false;

        files.forEach(file => {
            const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            const isValidType = validTypes.includes(file.type) || validExts.includes(ext);
            const isValidSize = file.size <= 50 * 1024 * 1024;

            // Check if file is already in selectedFiles to prevent UI duplicates
            const isDuplicate = selectedFiles.some(f => f.name === file.name && f.size === file.size);

            if (isValidType && isValidSize && !isDuplicate) {
                selectedFiles.push(file);
            } else if (!isValidType || !isValidSize) {
                invalidFound = true;
            }
        });

        if (invalidFound) {
            showStatus('Warning', 'Some files were skipped. Only PDF/DOCX under 50MB are supported.', 'error');
        }

        updateUI();
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        updateUI();
    }

    clearAllBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // prevent clicking dropzone
        selectedFiles = [];
        updateUI();
    });

    function updateUI() {
        fileCount.textContent = selectedFiles.length;

        if (selectedFiles.length > 0) {
            fileListContainer.classList.remove('hidden');

            // Rebuild list
            fileList.innerHTML = '';
            selectedFiles.forEach((file, index) => {
                const li = document.createElement('li');
                li.className = 'file-item';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'file-item-name';
                nameSpan.textContent = file.name;
                nameSpan.title = file.name;

                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'remove-btn';
                removeBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
                removeBtn.onclick = (e) => {
                    e.stopPropagation();
                    removeFile(index);
                };

                li.appendChild(nameSpan);
                li.appendChild(removeBtn);
                fileList.appendChild(li);
            });

            uploadTitle.innerHTML = 'Drop <span class="browse-text">more files</span> here';
        } else {
            fileListContainer.classList.add('hidden');
            fileList.innerHTML = '';
            uploadTitle.innerHTML = 'Drop files here, or <span class="browse-text">browse</span>';
        }

        checkFormValidity();
    }

    industrySelect.addEventListener('change', checkFormValidity);

    function checkFormValidity() {
        if (selectedFiles.length > 0 && industrySelect.value) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }

    // 3. Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (selectedFiles.length === 0 || !industrySelect.value) return;

        const formData = new FormData();
        formData.append('industry_id', industrySelect.value);

        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        setLoading(true);

        try {
            const response = await fetch('/api/v1/knowledge/batch_upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                let msg = `Total: ${result.total}, Success: ${result.success}`;
                let type = (result.failed && result.failed.length > 0) ? 'error' : 'success';

                if (result.duplicate > 0) {
                    msg += `. Skipped ${result.duplicate} duplicate(s)`;
                }
                if (result.failed && result.failed.length > 0) {
                    msg += `. Failed: ${result.failed.length}. Check console.`;
                    console.warn("Upload Failures:", result.failed);
                }

                showStatus(type === 'success' ? 'Batch Upload Complete' : 'Upload Finished with Issues', msg, type);

                // Clear successfully submitted if some succeeded
                if (result.success > 0 || result.total === result.duplicate) {
                    selectedFiles = [];
                    updateUI();
                    industrySelect.value = '';
                }
            } else {
                showStatus('Ingestion Failed', result.detail || 'An error occurred during API request.', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showStatus('Network Error', 'Could not connect to the server.', 'error');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            btnText.classList.add('hidden');
            loader.classList.remove('hidden');
        } else {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            checkFormValidity();
        }
    }

    function showStatus(title, message, type) {
        statusTitle.textContent = title;
        statusDesc.textContent = message;

        statusMessage.className = 'status-message';
        statusMessage.classList.add(type);

        const iconSvg = type === 'success'
            ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
            : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';

        statusMessage.querySelector('.status-icon').innerHTML = iconSvg;
    }

    closeStatus.addEventListener('click', () => {
        statusMessage.classList.add('hidden');
    });
});
