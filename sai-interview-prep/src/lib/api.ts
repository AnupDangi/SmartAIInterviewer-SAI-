/**
 * API client for backend communication
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


export interface Interview {
  id: string;
  user_id: string;
  title: string;
  duration_minutes: number;
  job_description: string | null;
  cv_summary: string | null;
  created_at: string;
}

export interface InterviewSession {
  id: string;
  interview_id: string;
  ai_message: string;
  user_message: string;
  feedback: string | null;
  created_at: string;
  session_run_id?: string;
}

export interface StartInterviewResponse {
  interview_id: string;
  session_run_id: string;  // NEW: Each start creates a new session run
  opening_question: string;
  interview_title: string;
  duration_minutes: number;
  cv_summary: string | null;
  jd_summary: string | null;
  status: string;
}

export interface SendMessageResponse {
  session_id: string;
  ai_message: string;
  feedback: string | null;
  created_at: string;
}

export interface User {
  id: string;  // For backward compatibility (same as user_id)
  user_id: string;  // Clerk user ID
  name: string | null;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface CreateInterviewRequest {
  title: string;
  duration_minutes?: number;
  // job_description will be processed by AI after upload
}

/**
 * Get auth headers with Clerk token
 */
export async function getAuthHeaders(token?: string, isFormData = false): Promise<HeadersInit> {
  const authToken = token || localStorage.getItem("clerk_token") || "";

  const headers: HeadersInit = {
    Authorization: `Bearer ${authToken}`,
  };

  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  return headers;
}

/**
 * API client functions
 */
export const api = {
  /**
   * Get current user
   */
  async getCurrentUser(token?: string): Promise<User> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/users/me`, {
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch user");
    }

    return response.json();
  },

  /**
   * Create a new interview (only title and duration)
   * job_description and cv_summary will be processed by AI after upload
   */
  async createInterview(
    data: CreateInterviewRequest,
    token?: string
  ): Promise<Interview> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/create`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to create interview" }));
      throw new Error(error.detail || "Failed to create interview");
    }

    return response.json();
  },

  /**
   * Process job description text (from textarea) with AI
   */
  async processJobDescriptionText(
    interviewId: string,
    text: string,
    token?: string
  ): Promise<{ message: string; interview_id: string; processed_length: number }> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/process-jd-text`, {
      method: "POST",
      headers,
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error("Failed to process job description");
    }

    return response.json();
  },

  /**
   * Upload CV for an interview
   */
  async uploadCV(
    interviewId: string,
    file: File,
    token?: string
  ): Promise<{ message: string; interview_id: string; filename: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = await getAuthHeaders(token, true);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/upload-cv`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to upload CV");
    }

    return response.json();
  },

  /**
   * Upload Job Description for an interview
   */
  async uploadJobDescription(
    interviewId: string,
    file: File,
    token?: string
  ): Promise<{ message: string; interview_id: string; filename: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = await getAuthHeaders(token, true);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/upload-jd`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to upload Job Description");
    }

    return response.json();
  },

  /**
   * Update an interview
   */
  async updateInterview(
    interviewId: string,
    data: { title?: string; duration_minutes?: number },
    token?: string
  ): Promise<Interview> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}`, {
      method: "PUT",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to update interview" }));
      throw new Error(error.detail || "Failed to update interview");
    }

    return response.json();
  },

  /**
   * Delete an interview
   */
  async deleteInterview(interviewId: string, token?: string): Promise<{ message: string; interview_id: string }> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}`, {
      method: "DELETE",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to delete interview" }));
      throw new Error(error.detail || "Failed to delete interview");
    }

    return response.json();
  },

  /**
   * Get all interviews for current user
   */
  async getInterviews(token?: string): Promise<Interview[]> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews`, {
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch interviews");
    }

    return response.json();
  },

  /**
   * Get a specific interview
   */
  async getInterview(interviewId: string, token?: string): Promise<Interview> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}`, {
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch interview");
    }

    return response.json();
  },

  /**
   * Get all sessions for an interview (optionally filtered by session_run_id)
   */
  async getInterviewSessions(
    interviewId: string,
    token?: string,
    sessionRunId?: string  // Optional: filter by session run
  ): Promise<InterviewSession[]> {
    const headers = await getAuthHeaders(token);
    const url = sessionRunId
      ? `${API_BASE_URL}/api/interviews/${interviewId}/sessions?session_run_id=${sessionRunId}`
      : `${API_BASE_URL}/api/interviews/${interviewId}/sessions`;
    const response = await fetch(url, {
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch interview sessions");
    }

    return response.json();
  },

  /**
   * Create a new interview session (conversation turn) - Legacy
   */
  async createInterviewSession(
    interviewId: string,
    data: { ai_message: string; user_message: string },
    token?: string
  ): Promise<InterviewSession> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/sessions`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error("Failed to create interview session");
    }

    return response.json();
  },

  /**
   * Start an interview session - generates opening question
   */
  async startInterview(
    interviewId: string,
    token?: string
  ): Promise<StartInterviewResponse> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/start`, {
      method: "POST",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to start interview" }));
      throw new Error(error.detail || "Failed to start interview");
    }

    return response.json();
  },

  /**
   * Send a message in the interview - AI generates response
   */
  async sendMessage(
    interviewId: string,
    userMessage: string,
    token?: string,
    sessionRunId?: string  // Optional: if not provided, uses most recent run
  ): Promise<SendMessageResponse> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/messages`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        user_message: userMessage,
        session_run_id: sessionRunId || null
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to send message" }));
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  },
  /**
   * End an interview session
   */
  async endInterview(
    interviewId: string,
    token?: string,
    sessionRunId?: string
  ): Promise<{ status: string; interview_id: string; session_run_id: string | null; summary?: string }> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/end`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        user_message: "END_SESSION", // Placeholder
        session_run_id: sessionRunId || null
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to end interview" }));
      throw new Error(error.detail || "Failed to end interview");
    }

    return response.json();
  },

  /**
   * Get the latest session for an interview
   */
  async getLatestSession(
    interviewId: string,
    token?: string
  ): Promise<InterviewSession | null> {
    const headers = await getAuthHeaders(token);
    const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}/latest-session`, {
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch latest session");
    }

    return response.json();
  },
};
