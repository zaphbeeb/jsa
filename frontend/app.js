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

// Main Tabs setup
document.querySelectorAll('.main-tab').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.main-tab-content').forEach(c => c.classList.add('hidden'));
        document.querySelectorAll('.main-tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-main-tab') + '-tab';
        document.getElementById(tabId).classList.remove('hidden');
        document.getElementById(tabId).classList.add('active');
    });
});

// Original Tabs setup (within Resume Parser)
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
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';
            li.style.alignItems = 'center';
            const dateStr = new Date(p.created_at).toLocaleDateString();
            
            li.innerHTML = `
                <div class="profile-info" style="display:flex; flex-direction:column; cursor:pointer; flex:1;">
                    <span class="name">${p.name}</span>
                    <span class="date">${dateStr}</span>
                </div>
                <div class="profile-actions" style="display:flex; gap:0.5rem;">
                    <button class="btn secondary small edit-profile-btn" data-id="${p.id}">Edit</button>
                    <button class="btn danger small delete-profile-btn" data-id="${p.id}">Del</button>
                </div>
            `;
            
            li.querySelector('.profile-info').addEventListener('click', () => fetchProfile(p.id));
            
            li.querySelector('.edit-profile-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                editProfileName(p.id, p.name);
            });

            li.querySelector('.delete-profile-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteProfile(p.id);
            });

            profilesList.appendChild(li);
        });
    } catch (err) {
        console.error("Failed to load profiles", err);
    }
}

async function editProfileName(id, currentName) {
    const newName = prompt("Enter new profile name:", currentName);
    if (!newName || newName.trim() === "" || newName === currentName) return;
    
    try {
        const req = await fetch(`${PROFILES_URL}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: newName })
        });
        if (req.ok) {
            loadProfiles();
        } else {
            throw new Error(await req.text());
        }
    } catch (err) {
        alert("Failed to update profile name: " + err.message);
    }
}

async function deleteProfile(id) {
    if (!confirm("Are you sure you want to delete this profile?")) return;
    
    try {
        const req = await fetch(`${PROFILES_URL}/${id}`, {
            method: 'DELETE'
        });
        if (req.ok) {
            loadProfiles();
        } else {
            throw new Error(await req.text());
        }
    } catch (err) {
        alert("Failed to delete profile: " + err.message);
    }
}

async function fetchProfile(id) {
    try {
        const req = await fetch(`${PROFILES_URL}/${id}`);
        const data = await req.json();
        handleResult(data.original_text || '', data.parsed_markdown);
        // Switch to resume-parser tab when loading a profile
        document.querySelector('[data-main-tab="resume-parser"]').click();
    } catch (err) {
        alert("Failed to load profile details.");
    }
}

// Company Tracker Logic
const trackJobsBtn = document.getElementById('track-jobs-btn');
const locationsInput = document.getElementById('locations-input');
const companiesInput = document.getElementById('companies-input');
const trackerResultsContent = document.getElementById('tracker-results-content');
const trackerLoading = document.getElementById('tracker-loading');
const jobCountBadge = document.getElementById('job-count-badge');

trackJobsBtn.addEventListener('click', async () => {
    const locations = locationsInput.value.trim();
    const companies = companiesInput.value.trim();
    
    if (!locations || !companies) {
        return alert("Please enter both locations and companies.");
    }
    
    setTrackerLoading(true);
    trackerResultsContent.innerHTML = '';
    jobCountBadge.classList.add('hidden');
    
    try {
        const req = await fetch('/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ locations, companies })
        });
        
        if (!req.ok) throw new Error(await req.text());
        
        const jobs = await req.json();
        renderTrackerResults(jobs);
    } catch (err) {
        alert("Error tracking jobs: " + err.message);
        trackerResultsContent.innerHTML = '<div class="empty-state"><p>Failed to load jobs. Please try again.</p></div>';
    } finally {
        setTrackerLoading(false);
    }
});

function setTrackerLoading(isLoading) {
    if (isLoading) {
        trackJobsBtn.classList.add('hidden');
        trackerLoading.classList.remove('hidden');
    } else {
        trackJobsBtn.classList.remove('hidden');
        trackerLoading.classList.add('hidden');
    }
}

function renderTrackerResults(jobs) {
    if (!jobs || jobs.length === 0) {
        trackerResultsContent.innerHTML = '<div class="empty-state"><p>No jobs found for these criteria.</p></div>';
        jobCountBadge.classList.add('hidden');
        return;
    }
    
    jobCountBadge.textContent = `${jobs.length} Roles`;
    jobCountBadge.classList.remove('hidden');
    
    trackerResultsContent.innerHTML = '';
    jobs.forEach(job => {
        const div = document.createElement('div');
        div.className = 'job-card';
        
        div.innerHTML = `
            <div class="job-header">
                <div class="job-title">${job.title}</div>
                <div class="badge">${job.company}</div>
            </div>
            <div class="job-meta">
                <span>📍 ${job.location}</span>
                ${job.date ? `<span>📅 ${job.date}</span>` : ''}
            </div>
            <div class="job-description">${job.description || 'No description available.'}</div>
            <div class="job-footer">
                <a href="${job.url}" target="_blank" class="btn secondary small">View Details</a>
            </div>
        `;
        trackerResultsContent.appendChild(div);
    });
}

// Init
window.addEventListener('DOMContentLoaded', loadProfiles);

