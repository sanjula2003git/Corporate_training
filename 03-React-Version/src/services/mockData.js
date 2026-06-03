// =====================================================================
// services/mockData.js
// Mock JSON data + tiny "service" functions.
// In a real app these would be HTTP calls (fetch/axios) to a backend.
// Keeping them here means components don't care WHERE data comes from.
// =====================================================================

export const students = [
  { id: "STU-001", name: "Ravi Kumar", email: "ravi.kumar@example.com", course: "React Fundamentals", status: "Active" },
  { id: "STU-002", name: "Meera Nair", email: "meera.nair@example.com", course: "Python Basics", status: "Active" },
  { id: "STU-003", name: "John Mathew", email: "john.mathew@example.com", course: "Java Backend", status: "Inactive" },
  { id: "STU-004", name: "Aisha Khan", email: "aisha.khan@example.com", course: "React Fundamentals", status: "Active" },
  { id: "STU-005", name: "David Lee", email: "david.lee@example.com", course: "Java Backend", status: "Active" },
];

export const trainers = [
  { id: "TRN-001", name: "Anita Sharma", expertise: "Java, Spring Boot", courses: "Java Backend, Microservices" },
  { id: "TRN-002", name: "Suresh Rao", expertise: "React, JavaScript", courses: "React Fundamentals" },
  { id: "TRN-003", name: "Priya Menon", expertise: "Python, Data Science", courses: "Python Basics, ML 101" },
];

export const courses = [
  { name: "React Fundamentals", trainer: "Suresh Rao", duration: "6 Weeks", status: "Ongoing" },
  { name: "Java Backend", trainer: "Anita Sharma", duration: "8 Weeks", status: "Ongoing" },
  { name: "Python Basics", trainer: "Priya Menon", duration: "4 Weeks", status: "Completed" },
];

export const certificates = [
  { student: "Meera Nair", course: "Python Basics", status: "Completed" },
  { student: "Ravi Kumar", course: "React Fundamentals", status: "In Progress" },
  { student: "John Mathew", course: "Java Backend", status: "Completed" },
];

export const recentActivities = [
  "New student Ravi Kumar enrolled in React Fundamentals.",
  "Trainer Anita Sharma assigned to Java Backend.",
  "Attendance saved for Python Basics (Batch 12).",
  "Certificate generated for Meera Nair.",
];

export const attendanceOverview = [
  { day: "Mon", value: 80 },
  { day: "Tue", value: 90 },
  { day: "Wed", value: 85 },
  { day: "Thu", value: 92 },
  { day: "Fri", value: 78 },
];

export const dashboardStats = {
  totalStudents: 248,
  totalTrainers: 18,
  totalCourses: 32,
  avgAttendance: "87%",
};

export const reportStats = {
  totalStudents: 248,
  completionRate: "74%",
  avgAttendance: "87%",
  certificatesIssued: 183,
  byCourse: [
    { course: "React Fundamentals", enrolled: 60, completed: 42, rate: "70%" },
    { course: "Java Backend", enrolled: 55, completed: 44, rate: "80%" },
    { course: "Python Basics", enrolled: 48, completed: 40, rate: "83%" },
  ],
};

// Simulate an async API fetch (returns a Promise after a short delay).
export function fetchData(dataset, delay = 300) {
  const map = { students, trainers, courses, certificates };
  return new Promise((resolve) => {
    setTimeout(() => resolve(map[dataset] ?? []), delay);
  });
}
