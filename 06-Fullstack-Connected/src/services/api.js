// =====================================================================
// services/api.js  —  the REAL data layer (replaces mockData.js)
//
// 🎯 THE WHOLE POINT OF THIS FOLDER:
//   In 03-React-Version every screen read from hard-coded arrays in
//   mockData.js. Here, every function below makes a real HTTP request to the
//   FastAPI backend (05-Backend-Database), which reads/writes the SQLite
//   database (training.db).
//
// This stage adds ROLE-BASED features: each person logs in with their own
// account and the backend returns only what their role is allowed to see —
// students, trainers and admins each get a different portal.
//
// HOW AUTH WORKS:
//   1. login() posts your username/password and gets back a JWT "access token"
//      plus your role and (for students/trainers) your linked record id.
//   2. We save those in the browser (localStorage).
//   3. Every protected request sends the token in "Authorization: Bearer ..."
// =====================================================================

// Where the backend lives. Start it with:
//   cd 05-Backend-Database && python -m uvicorn main:app --reload
const BASE_URL = "http://127.0.0.1:8000";

// ---------- token + identity storage (kept in the browser) ----------
export function getToken() {
  return localStorage.getItem("token");
}
export function getUser() {
  return {
    name: localStorage.getItem("userName") || "User",
    role: localStorage.getItem("userRole") || "",
    refId: localStorage.getItem("userRefId") || "",
  };
}
export function getRole() {
  return localStorage.getItem("userRole") || "";
}
export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("userName");
  localStorage.removeItem("userRole");
  localStorage.removeItem("userRefId");
}

// ---------- a tiny helper that every call below shares ----------
async function request(path, { method = "GET", body } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(BASE_URL + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------- AUTH ----------
export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const res = await fetch(BASE_URL + "/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) throw new Error("Incorrect username or password");

  const data = await res.json(); // { access_token, role, name, ref_id }
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("userName", data.name);
  localStorage.setItem("userRole", data.role);
  localStorage.setItem("userRefId", data.ref_id || "");
  return data;
}

// ---------- ROLE DASHBOARDS ----------
export const getStudentDashboard = () => request("/api/dashboard/student");
export const getTrainerDashboard = () => request("/api/dashboard/trainer");
export const getAdminDashboard = () => request("/api/dashboard/admin");

// ---------- STUDENTS / TRAINERS / COURSES (admin CRUD) ----------
export const getStudents = () => request("/api/students");
export const addStudent = (student) =>
  request("/api/students", { method: "POST", body: student });
export const deleteStudent = (id) =>
  request(`/api/students/${id}`, { method: "DELETE" });

export const getTrainers = () => request("/api/trainers");
export const addTrainer = (trainer) =>
  request("/api/trainers", { method: "POST", body: trainer });
export const deleteTrainer = (id) =>
  request(`/api/trainers/${id}`, { method: "DELETE" });

export const getCourses = () => request("/api/courses");
export const addCourse = (course) =>
  request("/api/courses", { method: "POST", body: course });
export const deleteCourse = (id) =>
  request(`/api/courses/${id}`, { method: "DELETE" });

// ---------- ADMINS (admin adds another admin) ----------
export const getUsers = () => request("/api/users");
export const addAdmin = (admin) =>
  request("/api/admins", { method: "POST", body: admin });

// ---------- MATERIALS ----------
export const getMaterials = () => request("/api/materials");
export const addMaterial = (material) =>
  request("/api/materials", { method: "POST", body: material });
export const deleteMaterial = (id) =>
  request(`/api/materials/${id}`, { method: "DELETE" });

// ---------- ASSIGNMENTS + SUBMISSIONS ----------
export const getAssignments = () => request("/api/assignments");
export const addAssignment = (assignment) =>
  request("/api/assignments", { method: "POST", body: assignment });
export const deleteAssignment = (id) =>
  request(`/api/assignments/${id}`, { method: "DELETE" });
export const submitAssignment = (assignmentId, body) =>
  request(`/api/assignments/${assignmentId}/submit`, { method: "POST", body });
export const getSubmissions = (assignmentId) =>
  request(`/api/assignments/${assignmentId}/submissions`);
export const getMySubmissions = () => request("/api/submissions/me");
export const gradeSubmission = (submissionId, body) =>
  request(`/api/submissions/${submissionId}/grade`, { method: "PUT", body });

// ---------- ONLINE CLASSES (Google Meet) ----------
export const getClasses = () => request("/api/classes");
export const addClass = (session) =>
  request("/api/classes", { method: "POST", body: session });
export const deleteClass = (id) =>
  request(`/api/classes/${id}`, { method: "DELETE" });

// ---------- ATTENDANCE ----------
export const getAttendance = () => request("/api/attendance");
export const getMyAttendance = () => request("/api/attendance/me");
export const saveAttendance = (record) =>
  request("/api/attendance", { method: "POST", body: record });

// ---------- CERTIFICATES ----------
export const getCertificates = () => request("/api/certificates");
export const generateCertificate = (student, course) =>
  request(
    `/api/certificates/generate?student=${encodeURIComponent(student)}&course=${encodeURIComponent(course)}`,
    { method: "POST" }
  );

// ---------- REPORTS ----------
export const getReports = () => request("/api/reports");

// ---------- SUPPORT CHAT ----------
// Student/trainer: send to (and read) their own thread with the admins.
// Admin: list all threads, read one, and reply (pass toUser).
export const sendChat = (message, toUser) =>
  request("/api/chat", { method: "POST", body: { message, to_user: toUser } });
export const getMyChat = () => request("/api/chat/me");
export const getChatThreads = () => request("/api/chat/threads");
export const getChatThread = (username) => request(`/api/chat/thread/${username}`);
