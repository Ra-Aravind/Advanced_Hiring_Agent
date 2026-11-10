const API_BASE = "http://127.0.0.1:8000/api/v1";

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { "Content-Type": "application/json" },
            ...options
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "API Error");
        return data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

const api = {
    // Auth
    login: (email, password) => fetchAPI("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

    // Candidates
    getCandidates: () => fetchAPI("/candidates/detailed"),

    // Interviewers
    getInterviewers: () => fetchAPI("/interviewers/detailed"),
    createInterviewer: (data) => fetchAPI("/interviewers", { method: "POST", body: JSON.stringify(data) }),
    deleteInterviewer: (id) => fetchAPI(`/interviewers/${id}`, { method: "DELETE" }),
    updateAvailability: (id, status) => fetchAPI(`/interviewers/${id}/availability`, {
        method: "PATCH",
        body: JSON.stringify({ availability_status: status })
    }),

    // Interviews
    getInterviews: () => fetchAPI("/interviews/detailed"),
    createInterview: (data) => fetchAPI("/interviews", { method: "POST", body: JSON.stringify(data) }),
    updateInterviewStatus: (id, status) => fetchAPI(`/interviews/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status })
    }),
    deleteInterview: (id) => fetchAPI(`/interviews/${id}`, { method: "DELETE" }),

    // Meetings
    generateMeeting: (id) => fetchAPI(`/meetings/${id}/create`, { method: "POST" }),

    // Feedback
    submitFeedback: (id, data) => fetchAPI(`/feedback/${id}`, { method: "POST", body: JSON.stringify(data) }),
    getFeedback: (id) => fetchAPI(`/feedback/${id}`),

    // AI
    runAIAnalysis: (id) => fetchAPI(`/ai/${id}/analyze`, { method: "POST" })
};
