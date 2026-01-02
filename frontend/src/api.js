import axios from 'axios';

const API_BASE_URL = '/api';  // Uses Vite proxy to backend

// Get available options for dropdowns
export const getOptions = async () => {
    const response = await axios.get(`${API_BASE_URL}/options`);
    return response.data;
};

// Get historical S% data
export const getHistoricalData = async (organism, antibiotic, ward = null) => {
    const params = { organism, antibiotic };
    if (ward) params.ward = ward;

    const response = await axios.get(`${API_BASE_URL}/historical`, { params });
    return response.data;
};

// Generate prediction
export const getPrediction = async (organism, antibiotic, ward = null) => {
    const response = await axios.post(`${API_BASE_URL}/predict`, {
        organism,
        antibiotic,
        ward: ward || null
    });
    return response.data;
};

// Get model performance comparison
export const getModelPerformance = async (organism = null, antibiotic = null) => {
    const params = {};
    if (organism) params.organism = organism;
    if (antibiotic) params.antibiotic = antibiotic;

    const response = await axios.get(`${API_BASE_URL}/model-performance`, { params });
    return response.data;
};

// Test API health
export const checkHealth = async () => {
    const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/health`);
    return response.data;
};
