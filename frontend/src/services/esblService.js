
import axios from 'axios';

// Base URL for the API
const API_URL = 'http://localhost:8000/api';

/**
 * ESBL CDSS Service
 * Handles all communication with the ESBL Risk & Recommendation Engine.
 */
export const esblService = {

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
    }
};
