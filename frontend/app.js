const UPLOAD_URL = '/api/parse/file';
const PASTE_URL = '/api/parse/text';
const PROFILES_URL = '/api/profiles';

let currentOriginalText = '';
let currentMarkdown = '';
let isEditing = false;

// Elements
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const textInput = document.getElementById('text-input');
const processBtn = document.getElementById('process-btn');
const loadingIndicator = document.getElementById('loading');
const resultContent = document.getElementById('result-content');
const editArea = document.getElementById('edit-area');
const editBtn = document.getElementById('edit-btn');
const saveBtn = document.getElementById('save-btn');
const saveDialog = document.getElementById('save-dialog');
const profileNameInput = document.getElementById('profile-name');
const confirmSaveBtn = document.getElementById('confirm-save-btn');
const cancelSaveBtn = document.getElementById('cancel-save-btn');
const profilesList = document.getElementById('profiles-list');

// Tabs setup
document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-tab') + '-tab';
        document.getElementById(tabId).classList.remove('hidden');
        document.getElementById(tabId).classList.add('active');
    });
});

// Drag and drop setup
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

dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
        fileInput.files = files;
        updateDropZoneText(files[0].name);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) updateDropZoneText(fileInput.files[0].name);
});

function updateDropZoneText(filename) {
    dropZone.querySelector('p').textContent = filename;
}

// Processing
processBtn.addEventListener('click', async () => {
    const activeTab = document.querySelector('.tab.active').getAttribute('data-tab');
    
    setLoading(true);
    
    try {
        if (activeTab === 'upload') {
            if (!fileInput.files.length) throw new Error("Please select a file.");
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            const req = await fetch(UPLOAD_URL, { method: 'POST', body: formData });
            if (!req.ok) throw new Error(await req.text());
            
            const res = await req.json();
            handleResult(res.extracted_text, res.markdown_result);
            
        } else {
            const text = textInput.value;
            if (!text.trim()) throw new Error("Please paste some text.");
            
            const req = await fetch(PASTE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({text: text})
            });
            if (!req.ok) throw new Error(await req.text());
            
            const res = await req.json();
            handleResult(res.extracted_text, res.markdown_result);
        }
    } catch (err) {
        alert("Error parsing resume: " + err.message);
    } finally {
        setLoading(false);
    }
});

function setLoading(isLoading) {
    if (isLoading) {
        processBtn.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
    } else {
        processBtn.classList.remove('hidden');
        loadingIndicator.classList.add('hidden');
    }
}

function handleResult(originalText, markdownResult) {
    currentOriginalText = originalText;
    currentMarkdown = markdownResult;
    
    renderMarkdown(currentMarkdown);
    
    editBtn.classList.remove('hidden');
    saveBtn.classList.remove('hidden');
}

function renderMarkdown(md) {
    const rawHtml = marked.parse(md);
    const cleanHtml = DOMPurify.sanitize(rawHtml);
    resultContent.innerHTML = cleanHtml;
}

// Editing
editBtn.addEventListener('click', () => {
    if (isEditing) {
        // Save edit
        currentMarkdown = editArea.value;
        renderMarkdown(currentMarkdown);
        editArea.classList.add('hidden');
        resultContent.classList.remove('hidden');
        editBtn.textContent = 'Edit Markdown';
        editBtn.classList.remove('success');
        editBtn.classList.add('secondary');
    } else {
        // Start edit
        editArea.value = currentMarkdown;
        resultContent.classList.add('hidden');
        editArea.classList.remove('hidden');
        editBtn.textContent = 'Preview';
        editBtn.classList.remove('secondary');
        editBtn.classList.add('success');
    }
    isEditing = !isEditing;
});

// Saving Profile
saveBtn.addEventListener('click', () => {
    saveDialog.classList.remove('hidden');
});

cancelSaveBtn.addEventListener('click', () => {
    saveDialog.classList.add('hidden');
    profileNameInput.value = '';
});

confirmSaveBtn.addEventListener('click', async () => {
    const name = profileNameInput.value;
    if (!name.trim()) return alert("Please enter a name");
    
    const data = {
        name,
        original_text: currentOriginalText,
        parsed_markdown: currentMarkdown
    };
    
    try {
        const req = await fetch(PROFILES_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (req.ok) {
            alert('Profile saved successfully!');
            saveDialog.classList.add('hidden');
            profileNameInput.value = '';
            loadProfiles();
        } else {
            throw new Error(await req.text());
        }
    } catch (err) {
        alert(err.message);
    }
});

// Load Profiles
async function loadProfiles() {
    try {
        const req = await fetch(PROFILES_URL);
        const profiles = await req.json();
        
        profilesList.innerHTML = '';
        if (profiles.length === 0) {
            profilesList.innerHTML = '<li style="color:var(--text-muted);font-size:0.9rem;">No saved profiles.</li>';
            return;
        }
        
        profiles.forEach(p => {
            const li = document.createElement('li');
            li.className = 'profile-item';
            const dateStr = new Date(p.created_at).toLocaleDateString();
            
            li.innerHTML = `
                <span class="name">${p.name}</span>
                <span class="date">${dateStr}</span>
            `;
            
            li.addEventListener('click', () => fetchProfile(p.id));
            profilesList.appendChild(li);
        });
    } catch (err) {
        console.error("Failed to load profiles", err);
    }
}

async function fetchProfile(id) {
    try {
        const req = await fetch(`${PROFILES_URL}/${id}`);
        const data = await req.json();
        handleResult(data.original_text || '', data.parsed_markdown);
    } catch (err) {
        alert("Failed to load profile details.");
    }
}

// Init
window.addEventListener('DOMContentLoaded', loadProfiles);
