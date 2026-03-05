import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
});

export const fetchDashboardSummary = () => api.get('/dashboard-summary').then(r => r.data);

export const fetchPlantMetrics = () => api.get('/plant-metrics').then(r => r.data);

export const fetchInverters = (params = {}) => api.get('/inverters', { params }).then(r => r.data);

export const fetchInverter = (id) => api.get(`/inverters/${id}`).then(r => r.data);

export const fetchInverterMetrics = (id) => api.get(`/inverters/${id}/metrics`).then(r => r.data);

export const fetchAlerts = (params = {}) => api.get('/alerts', { params }).then(r => r.data);

export const predictRisk = (payload) => api.post('/predict', payload).then(r => r.data);

export const askQuestion = (question) => api.post('/qa', { question }).then(r => r.data);

export default api;
