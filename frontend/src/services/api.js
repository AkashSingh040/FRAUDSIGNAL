import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary'),
};

export const casesApi = {
  list: () => api.get('/cases'),
  get: (id) => api.get(`/cases/${id}`),
  updateDecision: (id, decision, reason) => api.patch(`/cases/${id}`, { decision, reason }),
};

export const riskApi = {
  score: (tx) => api.post('/risk/score', tx),
  getStatus: () => api.get('/risk/status'),
};

export default api;
