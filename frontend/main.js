const API_BASE = "http://localhost:8000";


// 🔁 Fade transition helper
function fadeInContent(html) {
  const content = document.getElementById("content");
  content.classList.remove("fade-in");
  content.innerHTML = html;
  setTimeout(() => content.classList.add("fade-in"), 10);
}

function setThemeAccordingToSystem() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
}

document.addEventListener("DOMContentLoaded", () => {
    setThemeAccordingToSystem();
    const token = localStorage.getItem("token");
    token ? showDashboard() : showRegister();
});

// 📝 REGISTER
function showRegister() {
  fadeInContent(`
    <h3 class="text-center mb-3">Create an Account</h3>
    <p class="text-muted text-center">Welcome! Please enter your details.</p>
    <form onsubmit="register(event)">
      <label for="register-name">Name</label>
      <input type="text" class="form-control mb-2" id="register-name" required placeholder="Enter Your Name" autofocus />

      <label for="register-email">Email</label>
      <input type="email" class="form-control mb-2" id="register-email" required placeholder="Enter Your Email" />

      <label for="register-password">Password</label>
      <input type="password" class="form-control mb-3" id="register-password" required placeholder="********" />

      <button type="submit" class="btn btn-success"><i class="fas fa-user-plus me-2"></i>Sign Up</button>
    </form>

    <div class="text-center mt-3">
      <span class="text-muted">Already have an account?</span><br>
      <button class="btn btn-sm btn-outline-light mt-2" onclick="showLogin()">
        <i class="fas fa-sign-in-alt me-1"></i> Log in
      </button>
    </div>
  `);
}

// 🔐 LOGIN
function showLogin() {
  fadeInContent(`
    <h3 class="text-center mb-3">Login</h3>
    <form onsubmit="login(event)">
      <label for="login-email">Email</label>
      <input type="email" class="form-control mb-2" id="login-email" required placeholder="Enter Email" autofocus />

      <label for="login-password">Password</label>
      <input type="password" class="form-control mb-3" id="login-password" required placeholder="********" />

      <button type="submit" class="btn btn-primary"><i class="fas fa-sign-in-alt me-2"></i>Login</button>
    </form>

    <div class="text-center mt-3">
      <span class="text-muted">Don't have an account?</span><br>
      <button class="btn btn-sm btn-outline-light mt-2" onclick="showRegister()">
        <i class="fas fa-user-plus me-1"></i> Register
      </button>
    </div>
  `);
}

// ✅ REGISTER → BACKEND
async function register(event) {
  event.preventDefault();
  const name = document.getElementById("register-name").value;
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ Name: name, email, password, role: "candidate" })
    });

    if (!res.ok) throw new Error((await res.json()).detail || "Registration failed");
    alert("OTP sent to your email.");
    showOtpVerification(email);
  } catch (err) {
    alert("Registration error: " + err.message);
  }
}

// 🔐 OTP VERIFICATION
function showOtpVerification(email) {
  fadeInContent(`
    <h3 class="text-center mb-3">Verify OTP</h3>
    <form onsubmit="verifyOtp(event, '${email}')">
      <input type="text" class="form-control mb-3" id="otp" placeholder="Enter OTP" required autofocus />
      <button type="submit" class="btn btn-primary">
        <i class="fas fa-key me-2"></i>Verify OTP
      </button>
    </form>
  `);
}

async function verifyOtp(event, email) {
  event.preventDefault();
  const otp = document.getElementById("otp").value;

  try {
    const res = await fetch(`${API_BASE}/auth/verify-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp })
    });

    if (!res.ok) throw new Error((await res.json()).detail || "OTP verification failed");
    alert("Account verified! You can now log in.");
    showLogin();
  } catch (err) {
    alert("OTP verification error: " + err.message);
  }
}

// ✅ LOGIN → DASHBOARD
async function login(event) {
  event.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) throw new Error((await res.json()).detail || "Login failed");

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    showDashboard();
  } catch (err) {
    alert("Login error: " + err.message);
  }
}  

// ✅ DASHBOARD WITH NAME, ROLE, AVATAR
async function showDashboard() {
  const token = localStorage.getItem("token");

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) throw new Error("Failed to fetch user profile");

    const data = await res.json();
    const name = data.Name || "User";
    const email = data.email;
    const role = data.role;
    const avatar = data.avatar_url
      ? `${API_BASE}${data.avatar_url}`
      : `${API_BASE}/media/avatars/avatar-15-128.png`;

    fadeInContent(`
      <div class="text-center">
        <img src="${avatar}" class="rounded-circle mb-3" width="100" height="100" alt="Avatar" />
        <h4>${name}</h4>
        <p class="text-muted">${email}</p>
        <span class="badge bg-info text-dark text-capitalize">${role}</span>
      </div>

      <div class="mt-4">
        <button class="btn btn-outline-light w-100" onclick="showEditProfile()">✏️ Edit Profile</button>
        <button class="btn btn-outline-warning mt-2 w-100" onclick="showChangePassword()">🔐 Change Password</button>
        <button class="btn btn-danger mt-2 w-100" onclick="logout()">
          <i class="fas fa-sign-out-alt me-2"></i>Logout
        </button>
        <button class="btn btn-success mt-2 w-100" onclick="startRealInterviewFlow()">
            🎥 Start Interview
        </button>

      </div>
    `);
  } catch (err) {
    alert("Error loading dashboard: " + err.message);
    logout();
  }
}

// ✅ EDIT PROFILE SCREEN
function showEditProfile() {
  fadeInContent(`
    <h3 class="text-center mb-3">Edit Profile</h3>
    <form onsubmit="submitProfileUpdate(event)">
      <label>Name</label>
      <input type="text" id="edit-name" class="form-control mb-2" required placeholder="New Name" autofocus />

      <label>Upload Avatar</label>
      <input type="file" id="avatar-file" class="form-control mb-3" accept="image/*" />

      <button type="submit" class="btn btn-success w-100">Save Changes</button>
      <button type="button" class="btn btn-secondary w-100 mt-2" onclick="showDashboard()">Cancel</button>
    </form>
  `);
}

// ✅ SUBMIT PROFILE UPDATE (Name + Avatar)
async function submitProfileUpdate(event) {
  event.preventDefault();
  const token = localStorage.getItem("token");
  const newName = document.getElementById("edit-name").value;
  const avatarFile = document.getElementById("avatar-file").files[0];

  try {
    await fetch(`${API_BASE}/users/me`, {
      method: "PATCH",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ Name: newName })
    });

    if (avatarFile) {
      const formData = new FormData();
      formData.append("file", avatarFile);

      await fetch(`${API_BASE}/users/me/avatar`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
    }

    alert("Profile updated!");
    showDashboard();
  } catch (err) {
    alert("Update failed: " + err.message);
  }
}

// ✅ SHOW CHANGE PASSWORD FORM
function showChangePassword() {
  fadeInContent(`
    <h3 class="text-center mb-3">Change Password</h3>
    <form onsubmit="submitPasswordChange(event)">
      <label>Old Password</label>
      <input type="password" id="old-password" class="form-control mb-2" required placeholder="Enter old password" />

      <label>New Password</label>
      <input type="password" id="new-password" class="form-control mb-2" required placeholder="New password" />

      <label>Confirm New Password</label>
      <input type="password" id="confirm-password" class="form-control mb-3" required placeholder="Confirm password" />

      <button type="submit" class="btn btn-success w-100">Update Password</button>
      <button type="button" class="btn btn-secondary w-100 mt-2" onclick="showDashboard()">Cancel</button>
    </form>
  `);
}

// ✅ SUBMIT PASSWORD CHANGE TO BACKEND
async function submitPasswordChange(event) {
  event.preventDefault();
  const token = localStorage.getItem("token");
  const oldPassword = document.getElementById("old-password").value;
  const newPassword = document.getElementById("new-password").value;
  const confirmPassword = document.getElementById("confirm-password").value;

  if (newPassword !== confirmPassword) {
    alert("New passwords do not match!");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/users/me/change-password`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword
      })
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Password change failed");
    }

    alert("Password updated successfully!");
    showDashboard();

  } catch (err) {
    alert("Error: " + err.message);
  }
}

// 🚪 LOGOUT
function logout() {
  localStorage.clear();
  showLogin();
}
  
let questionList = [];
let currentIndex = 0;
let recordedAnswers = [];
let globalInterviewId = null;
let globalUserId = null;
let timerInterval = null;
let recordingStopped = false;
let mediaRecorder;
let recordedChunks = [];
let feedbackList = [];

const QUESTION_TIME_LIMIT = 60; // seconds

async function getCurrentUser() {
    const token = localStorage.getItem("token");
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  
    if (!res.ok) throw new Error("Failed to fetch current user");
  
    return await res.json();
  }

  async function startRealInterviewFlow() {
    try {
      const user = await getCurrentUser();
      globalUserId = user.client_id;
  
      // Fetch real questions
      const res = await fetch(`${API_BASE}/api/questions?limit=5`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
  
      const questions = await res.json();
      questionList = questions.sort(() => 0.5 - Math.random());
  
      const questionIds = questionList.map(q => q._id);
      const interview = await createInterview(questionIds);
  
      globalInterviewId = interview.id;
      currentIndex = 0;
      recordedAnswers = [];
  
      showQuestionScreen();
    } catch (err) {
      alert("Failed to start interview: " + err.message);
    }
  }
  
  // ✅ Updated to accept question IDs
  async function createInterview(questionIds) {
    const token = localStorage.getItem("token");
  
    const res = await fetch(`${API_BASE}/api/interviews/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ questions: questionIds })
    });
  
    if (!res.ok) throw new Error("Failed to create interview");
  
    return await res.json();
}  

// ✅ Move this function higher in the file
async function setupCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  document.getElementById('preview').srcObject = stream;
  window.mediaStream = stream;

  const recordedChunks = [];
  const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

  recorder.ondataavailable = e => recordedChunks.push(e.data);

  recorder.onstop = async () => {
    const blob = new Blob(recordedChunks, { type: "video/webm" });

    const tempVideo = document.createElement("video");
    tempVideo.src = URL.createObjectURL(blob);

    tempVideo.onloadedmetadata = async () => {
      if (tempVideo.duration < 1) {
        alert("Recording failed or is too short.");
        return;
      }

      await uploadAnswer(blob);
      currentIndex++;
      if (currentIndex < questionList.length) {
        recordingStopped = false;
        setTimeout(showQuestionScreen, 500);
      } else {
        finishInterview();
      }
    };
  };

  window.mediaRecorder = recorder;
}

function showQuestionScreen() {
  const q = questionList[currentIndex];
  fadeInContent(`
    <h5>Question ${currentIndex + 1} of ${questionList.length}</h5>
    <p>${q.question}</p>
    <div id="timer" class="badge bg-warning text-dark fs-6 mb-2">Time left: ${QUESTION_TIME_LIMIT}s</div>
    <div id="recording-status" class="mb-2"></div>
    <video id="preview" width="100%" autoplay muted playsinline class="mb-2 border rounded"></video>

    <div class="d-grid gap-2">
      <button id="startBtn" class="btn btn-primary" onclick="startRecording()">⏺️ Start</button>
      <button id="stopBtn" class="btn btn-danger" onclick="stopRecording()" disabled>⏹️ Stop</button>
    </div>
  `);

  setupCamera();
  startCountdown(QUESTION_TIME_LIMIT);
}


function startCountdown(seconds) {
  let timeLeft = seconds;
  const timer = document.getElementById("timer");
  timerInterval = setInterval(() => {
    timeLeft--;
    timer.textContent = `Time left: ${timeLeft}s`;
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      stopRecording();
    }
  }, 1000);
}

function startRecording() {
  recordedChunks = [];
  const startBtn = document.getElementById("startBtn");
  const stopBtn = document.getElementById("stopBtn");

  startBtn.disabled = true;
  stopBtn.disabled = false;

  document.getElementById("recording-status").innerHTML = `
    <span class="badge bg-danger text-light">🔴 Recording...</span>
  `;

  mediaRecorder = new MediaRecorder(window.mediaStream, { mimeType: 'video/webm' });

  mediaRecorder.ondataavailable = e => recordedChunks.push(e.data);

  mediaRecorder.onstop = async () => {
    const blob = new Blob(recordedChunks, { type: "video/webm" });
    const url = URL.createObjectURL(blob);
    const tempVideo = document.createElement("video");
    tempVideo.src = url;

    tempVideo.onloadedmetadata = async () => {
      if (tempVideo.duration < 1) {
        alert("Recording failed or is too short.");
        return;
      }

      await uploadAnswer(blob);
      currentIndex++;
      if (currentIndex < questionList.length) {
        recordingStopped = false;
        setTimeout(showQuestionScreen, 500);
      } else {
        finishInterview();
      }
    };
  };

  mediaRecorder.start();
}

function stopRecording() {
  if (recordingStopped || !mediaRecorder || mediaRecorder.state !== "recording") return;
  recordingStopped = true;

  clearInterval(timerInterval);
  mediaRecorder.stop();

  const videoEl = document.getElementById("preview");
  if (videoEl) {
    videoEl.pause();
    videoEl.srcObject = null;
  }

  if (window.mediaStream) {
    window.mediaStream.getTracks().forEach(track => track.stop());
  }

  document.getElementById("startBtn").disabled = false;
  document.getElementById("stopBtn").disabled = true;
  document.getElementById("recording-status").innerHTML = `
  <span class="spinner-border spinner-border-sm me-2"></span> Uploading...
`;
}

async function uploadAnswer(blob) {
  const formData = new FormData();
  formData.append("video", blob, `question${currentIndex + 1}.webm`);
  formData.append("user_id", globalUserId);
  formData.append("interview_id", globalInterviewId);

  const res = await fetch(`${API_BASE}/api/interviews/${globalInterviewId}/analyze/final`, {
    method: "POST",
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    body: formData
  });

  const data = await res.json();
  localStorage.setItem("last_ai_result", JSON.stringify(data)); // 👈 Save it
  console.log("AI Feedback", data);
}


function showFeedbackScreen(data) {
  fadeInContent(`
    <h3 class="mb-3">📊 AI Feedback</h3>
    <p>${data.feedback_for_candidate}</p>

    <div class="mb-4">
      <canvas id="facialChart" height="200"></canvas>
    </div>

    <div class="mb-4">
      <canvas id="speechChart" height="200"></canvas>
    </div>

    <button class="btn btn-primary w-100" onclick="showDashboard()">Return to Dashboard</button>
  `);

  setTimeout(() => {
    renderFacialChart(data.facial_summary);
    renderSpeechChart(data.speech_analysis);
  }, 200); // Slight delay to ensure canvas is rendered
}
function renderFacialChart(summary) {
  const ctx = document.getElementById("facialChart").getContext("2d");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: Object.keys(summary),
      datasets: [{
        label: "Facial Emotions",
        data: Object.values(summary),
        backgroundColor: [
          "#f94144", "#f3722c", "#f9844a", "#90be6d", "#43aa8b", "#577590"
        ]
      }]
    }
  });
}
function renderSpeechChart(analysis) {
  const ctx = document.getElementById("speechChart").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Speech Clarity", "Speech Rate"],
      datasets: [{
        label: "Speech Metrics",
        data: [analysis.speech_score || 0, analysis.speech_rate || 0],
        backgroundColor: ["#007bff", "#6f42c1"]
      }]
    },
    options: {
      scales: {
        y: { beginAtZero: true, max: 10 }
      }
    }
  });
}

async function renderCharts() {
  try {
    const res = await fetch(`${API_BASE}/api/interviews/${globalInterviewId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    const data = await res.json();

    const facial = data.facial_analysis || {};
    const speech = data.speech_analysis || {};
    const sentiment = data.feedback_for_candidate || "Not available";

    // Update sentiment summary
    document.getElementById("sentiment-summary").innerText = sentiment;

    // Chart 1: Facial emotions pie
    new Chart(document.getElementById("emotionChart"), {
      type: 'pie',
      data: {
        labels: Object.keys(facial),
        datasets: [{
          data: Object.values(facial),
          backgroundColor: ['#f44336', '#4caf50', '#2196f3', '#ffeb3b', '#9c27b0']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Facial Emotion Distribution'
          }
        }
      }
    });

    // Chart 2: Speech clarity score bar
    new Chart(document.getElementById("speechChart"), {
      type: 'bar',
      data: {
        labels: ['Speech Clarity'],
        datasets: [{
          label: 'Score (out of 10)',
          data: [speech.clarity_score || 0],
          backgroundColor: '#00bcd4'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Speech Clarity'
          }
        },
        scales: {
          y: { beginAtZero: true, max: 10 }
        }
      }
    });
  } catch (err) {
    console.error("Error loading feedback charts", err);
  }
}

function showInterviewReviewScreen(feedbackList) {
  let html = `
    <h3 class="text-center mb-3">Interview Review 🎯</h3>
    <div class="accordion" id="feedbackAccordion">
  `;

  feedbackList.forEach((entry, i) => {
    const canvasId1 = `emotionChart${i}`;
    const canvasId2 = `clarityChart${i}`;

    html += `
      <div class="accordion-item">
        <h2 class="accordion-header" id="heading${i}">
          <button class="accordion-button ${i !== 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${i}">
            Question ${i + 1}
          </button>
        </h2>
        <div id="collapse${i}" class="accordion-collapse collapse ${i === 0 ? 'show' : ''}" data-bs-parent="#feedbackAccordion">
          <div class="accordion-body">
            <p><strong>Q:</strong> ${entry.question}</p>
            <video src="${entry.videoUrl}" controls class="w-100 mb-2"></video>
            <p><strong>Feedback:</strong> ${entry.feedback}</p>
            <canvas id="${canvasId1}" height="120"></canvas>
            <canvas id="${canvasId2}" height="120" class="mt-3"></canvas>
          </div>
        </div>
      </div>
    `;
  });

  html += `</div>
    <button class="btn btn-outline-light w-100 mt-4" onclick="showDashboard()">Return to Dashboard</button>
  `;

  fadeInContent(html);

  // Generate charts after rendering
  setTimeout(() => {
    feedbackList.forEach((entry, i) => {
      createPieChart(`emotionChart${i}`, entry.facial || {});
      createRadarChart(`clarityChart${i}`, entry.speech || {});
    });
  }, 500);
}

function createPieChart(id, data) {
  const labels = Object.keys(data);
  const values = Object.values(data);

  new Chart(document.getElementById(id), {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        label: 'Facial Emotions',
        data: values,
        backgroundColor: ['#ff6384', '#36a2eb', '#ffcd56', '#4bc0c0', '#9966ff']
      }]
    }
  });
}

function createRadarChart(id, data) {
  const labels = Object.keys(data);
  const values = Object.values(data);

  new Chart(document.getElementById(id), {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Speech Analysis',
        data: values,
        fill: true,
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgb(54, 162, 235)',
        pointBackgroundColor: 'rgb(54, 162, 235)'
      }]
    },
    options: {
      elements: {
        line: { borderWidth: 2 }
      }
    }
  });
}

function finishInterview() {
  fadeInContent(`<h3>Interview Complete 🎉</h3>
    <p>Here is your AI analysis summary.</p>
    <div class="mb-3">
      <canvas id="facialChart" height="200"></canvas>
    </div>
    <div class="mb-3">
      <canvas id="speechChart" height="200"></canvas>
    </div>
    <button class="btn btn-outline-light mt-3 w-100" onclick="showDashboard()">Return to Dashboard</button>
  `);

  fetch(`${API_BASE}/api/interviews/${globalInterviewId}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
  })
    .then(res => res.json())
    .then(interview => {
      const feedback = interview.ai_feedback?.slice(-1)[0]?.feedback || "No feedback found";
      const facial = interview.ai_feedback?.slice(-1)[0]?.facial_analysis || {};
      const speech = interview.ai_feedback?.slice(-1)[0]?.speech_analysis || {};

      renderCharts(facial, speech);
    });
}

function renderCharts(facial, speech) {
  const facialData = {
    labels: Object.keys(facial || {}),
    datasets: [{
      label: "Facial Emotions",
      data: Object.values(facial || {}),
      backgroundColor: ["#f87171", "#facc15", "#34d399", "#60a5fa", "#c084fc"],
    }],
  };

  const speechData = {
    labels: ["Speech Clarity", "Sentiment"],
    datasets: [{
      label: "Speech Analysis",
      data: [speech.clarity || 0, speech.sentiment_score || 0],
      backgroundColor: ["#38bdf8", "#fbbf24"],
    }],
  };

  new Chart(document.getElementById("facialChart"), {
    type: "bar",
    data: facialData,
    options: { responsive: true }
  });

  new Chart(document.getElementById("speechChart"), {
    type: "radar",
    data: speechData,
    options: { responsive: true }
  });
}

  const facial = lastResult.facial_summary || {};
  const speech = lastResult.speech_analysis || {};
  const feedback = lastResult.feedback_for_candidate || "Feedback not available";
  const sentiment = speech.sentiment || "Not available";
  const clarity = speech.clarity_score || 0;

  fadeInContent(`
    <h3 class="text-center">Interview Complete 🎉</h3>
    <p class="text-center">Here is your AI analysis summary.</p>

    <canvas id="emotionChart" class="mb-3"></canvas>
    <div class="text-center">
      <p><strong>Speech Clarity:</strong> ${clarity}/10</p>
      <p><strong>Sentiment:</strong> ${sentiment}</p>
      <p><strong>AI Feedback:</strong><br>${feedback}</p>
    </div>

    <button class="btn btn-primary w-100 mt-3" onclick="showDashboard()">Return to Dashboard</button>
  `);

  setTimeout(() => {
    renderEmotionChart(facial);
  }, 500);


function renderEmotionChart(summary) {
  const ctx = document.getElementById('emotionChart').getContext('2d');
  const emotions = Object.keys(summary);
  const counts = Object.values(summary);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: emotions,
      datasets: [{
        label: 'Emotion Distribution',
        data: counts,
        backgroundColor: 'rgba(54, 162, 235, 0.6)'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}


