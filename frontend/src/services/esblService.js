
import axios from 'axios';

// Base URL for the API
const API_URL = 'http://localhost:8000/api';

// Mock DB for demo continuity (simulates backend persistence)
const mockEncounters = new Map();

/**
 * ESBL CDSS Service
 * Handles all communication with the ESBL Risk & Recommendation Engine.
 */
export const esblService = {
    /**
     * Store encounter data (Inputs + Prediction)
     */
    async saveEncounter(id, data) {
        try {
            await axios.post(`${API_URL}/encounters`, data);
            console.log("Saved Encounter to Backend:", id);
        } catch (error) {
            console.error("Backend Save Failed, falling back to local:", error);
            mockEncounters.set(id, { ...data, timestamp: new Date() });
        }
    },

    /**
     * Retrieve encounter data
     */
    async getEncounter(id) {
        try {
            const response = await axios.get(`${API_URL}/encounters/${id}`);
            return response.data;
        } catch (error) {
            console.warn("Backend Fetch Failed, checking local:", error);
            // Fallback for demo flow if backend is offline
            return mockEncounters.get(id);
        }
    },

    /**
     * Submit Final AST Results to Supabase (ast_manual_entry)
     */
    async persistASTResults(encounterId, astData, inputContext) {
        // Transform the key-value AST data to the Array format expected by /api/entry
        const payload = {
            lab_no: encounterId,
            age: inputContext?.Age ? parseInt(inputContext.Age) : 0,
            gender: inputContext?.Gender || "Unknown",
            bht: "BHT-" + encounterId.split('-')[1], // Generate pseudo-BHT from ID
            ward: inputContext?.Ward || "Unknown",
            specimen_type: inputContext?.Sample_Type || "Unknown",
            organism: inputContext?.Organism || "Unknown",
            results: Object.entries(astData).map(([antibiotic, result]) => ({
                antibiotic,
                result: result.toUpperCase() // Ensure 'S', 'I', 'R'
            }))
        };

        console.log("Saving to Supabase:", payload);
        return axios.post(`${API_URL}/entry`, payload);
    },

    /**
     * Stage 8/9: Check Scope Eligibility.
     * Prevents UI from proceeding if organism/gram is out of scope.
     */
    async validateScope(organism, gram) {
        try {
            const response = await axios.post(`${API_URL}/esbl/validate-scope`, {
                organism,
                gram
            });
            return response.data; // { allowed: bool, reason: str }
        } catch (error) {
            console.error('Scope Validation Failed:', error);
            throw error;
        }
    },

    /**
     * Stage 9: Main CDSS Engine.
     * Returns Risk, Recommendations, Metadata, and Warnings.
     * HARD STOP if ast_available is true (handled by backend 403).
     */
    async evaluateCase(inputs, astAvailable = false) {
        try {
            const response = await axios.post(`${API_URL}/esbl/evaluate`, {
                inputs,
                ast_available: astAvailable
            });
            return response.data;
        } catch (error) {
            if (error.response && error.response.status === 403) {
                throw new Error("GOVERNANCE LOCK: Empiric prediction is disabled when AST is available.");
            }
            throw error;
        }
    },

    /**
     * Stage 8: Audit Logging for Clinician Overrides.
     */
    async logDecision(auditData) {
        // auditData = { encounter_id, user_id, model_version, decision, reason_code, ... }
        return axios.post(`${API_URL}/esbl/override`, auditData);
    },

    /**
     * Stage 8C: Post-AST Confirmation.
     */
    async getPostASTReview(empiricDrug, astPanel) {
        return axios.post(`${API_URL}/esbl/post-ast-review`, {
            empiric_drug: empiricDrug,
            ast_panel: astPanel
        });
    },

    /**
     * Stage 9: Gov Audit Logs.
     */
    async getAuditLogs() {
        const response = await axios.get(`${API_URL}/esbl/audit-logs`);
        return response.data;
    },

    /**
     * Master Data: Fetch Definitions (Ward, SampleType)
     */
    async getMasterDefinitions(category) {
        // category: 'WARD' or 'SAMPLE_TYPE'
        try {
            const response = await axios.get(`${API_URL}/master/definitions/${category}`);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch master data for ${category}:`, error);
            return [];
        }
    }
};
