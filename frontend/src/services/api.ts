import axios from 'axios';

const rawApiBaseUrl = import.meta.env.VITE_API_URL || '/api';
export const API_BASE_URL = rawApiBaseUrl.endsWith('/api') ? rawApiBaseUrl : `${rawApiBaseUrl}/api`;

export interface AppErrorInfo {
  title: string;
  message: string;
  hint?: string;
  status?: number;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {'Content-Type': 'application/json'},
});

const buildErrorInfo = (status: number | undefined, detail: string | undefined, fallbackMessage: string): AppErrorInfo => {
  const normalizedDetail = detail?.trim();

  if (!status) {
    return {
      title: 'Connection problem',
      message: fallbackMessage,
      hint: 'Check that the frontend and backend are both running, then try again.',
    };
  }

  if (status === 400 && normalizedDetail?.toLowerCase().includes('invalid arxiv url')) {
    return {
      title: 'Invalid arXiv URL',
      message: normalizedDetail,
      hint: 'Use a standard arXiv abstract or PDF link, such as https://arxiv.org/abs/2301.12345.',
      status,
    };
  }

  if (status === 401) {
    return {
      title: 'Session expired',
      message: normalizedDetail || 'Your sign-in session is no longer valid.',
      hint: 'Sign in again, then retry the action.',
      status,
    };
  }

  if (status === 404 && normalizedDetail?.toLowerCase().includes('paper not found on arxiv')) {
    return {
      title: 'Paper not found on arXiv',
      message: normalizedDetail,
      hint: 'Check the arXiv URL and confirm that the paper is publicly available.',
      status,
    };
  }

  if (status === 404 && normalizedDetail?.toLowerCase().includes('share link')) {
    return {
      title: 'Share link unavailable',
      message: normalizedDetail,
      hint: 'Ask the owner for a fresh share link if you still need access.',
      status,
    };
  }

  if (status === 429) {
    return {
      title: 'Too many requests',
      message: normalizedDetail || fallbackMessage,
      hint: 'Wait a minute, then try again.',
      status,
    };
  }

  if (status === 502 || status === 503 || status === 504) {
    return {
      title: 'Upstream service unavailable',
      message: normalizedDetail || fallbackMessage,
      hint: 'The backend could not reach a required upstream service. Retry in a moment.',
      status,
    };
  }

  if (status >= 500) {
    return {
      title: 'Server error',
      message: normalizedDetail || fallbackMessage,
      hint: 'Retry the request. If it keeps failing, inspect the backend logs.',
      status,
    };
  }

  return {
    title: 'Request failed',
    message: normalizedDetail || fallbackMessage,
    status,
  };
};

export const getApiErrorInfo = (error: unknown, fallbackMessage: string): AppErrorInfo => {
  if (axios.isAxiosError(error)) {
    const detail = typeof error.response?.data?.detail === 'string'
      ? error.response.data.detail
      : error.message;
    return buildErrorInfo(error.response?.status, detail, fallbackMessage);
  }

  if (error instanceof Error) {
    return buildErrorInfo(undefined, error.message, fallbackMessage);
  }

  return buildErrorInfo(undefined, undefined, fallbackMessage);
};

// Error interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthRequest = requestUrl.includes('/auth/request-link') || requestUrl.includes('/auth/verify') || requestUrl.includes('/auth/me');

    if (error.response?.status === 401 && !isAuthRequest) {
      // Clear auth state and redirect to home
      localStorage.removeItem('auth-storage');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  requestMagicLink: async (email: string) => {
    const response = await api.post('/auth/request-link', { email });
    return response.data;
  },
  verifyMagicLink: async (token: string) => {
    const response = await api.post('/auth/verify', { token });
    return response.data;
  },
  getSessionUser: async (token: string) => {
    const response = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};

export const papersAPI = {
  analyze: async (arxivUrl: string, token: string) => {
    const response = await api.post('/papers/analyze', { arxiv_url: arxivUrl },
      { headers: { Authorization: `Bearer ${token}` } });
    return response.data;
  },
  getAnalysis: async (paperId: string, token: string) => {
    const response = await api.get(`/papers/${paperId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  listPapers: async (token: string) => {
    const response = await api.get('/papers', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
};

export const shareAPI = {
  createShareLink: async (paperId: string, token: string) => {
    const response = await api.post(`/papers/${paperId}/share`, null, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
  getSharedPaper: async (shareToken: string) => {
    const response = await api.get(`/share/${shareToken}`);
    return response.data;
  },
};

export default api;
