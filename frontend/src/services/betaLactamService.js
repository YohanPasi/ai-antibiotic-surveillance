
import axios from 'axios';

// Base URL for the API
const API_URL = `${import.meta.env.VITE_API_URL}/api`;

// Local fallback map (used when backend is unavailable — demo resilience)
const mockEncounters = new Map();

/**
 * Beta-Lactam Resistance Spectrum CDSS Service
 * Replaces: esblService.js
 *
 * Handles all communication with the Beta-Lactam Spectrum Engine API.
 * The API returns susceptibility probabilities + traffic lights
 * per beta-lactam generation (Gen1, Gen2, Gen3, Gen4, Carbapenem, BL_Combo).
 */
export const betaLactamService = {

    /**
     * Store encounter data (inputs + spectrum prediction) to backend.
     * Falls back to local Map on failure for demo continuity.
     */
    async saveEncounter(id, data) {
        try {
            await axios.post(`${API_URL}/beta-lactam/encounters`, data);
            console.log('✅ Encounter saved to backend:', id);
        } catch (error) {
            console.warn('Backend save failed — using local fallback:', error.message);
            mockEncounters.set(id, { ...data, timestamp: new Date() });
        }
    },

    /**
     * Retrieve an encounter from the backend (or local fallback).
     */
    async getEncounter(id) {
        try {
            const response = await axios.get(`${API_URL}/beta-lactam/encounters/${id}`);
            return response.data;
        } catch (error) {
            console.warn('Backend fetch failed — checking local:', error.message);
            return mockEncounters.get(id) || null;
        }
    },

    /**
     * Submit confirmed AST lab results to the backend.
     * Transforms { antibiotic: result } key-value pairs into the
     * array format expected by POST /api/entry (lab entry endpoint).
     */
    async persistASTResults(encounterId, astData, inputContext) {
        const payload = {
            encounter_id: encounterId,
            lab_no: encounterId,
            bht: 'BHT-' + (encounterId.split('-')[1] || encounterId),
            ward: inputContext?.Ward || 'Unknown',
            specimen_type: inputContext?.Sample_Type || 'Unknown',
            organism: inputContext?.Organism || 'Unknown',
            results: Object.entries(astData).map(([antibiotic, result]) => ({
                antibiotic,
                result: result.toUpperCase()   // Enforce S / I / R
            }))
        };

        console.log('Saving AST results to backend:', payload);
        return axios.post(`${API_URL}/beta-lactam/lab-results`, payload);
    },

    /**
     * Scope governance check.
     * Prevents UI from proceeding with out-of-scope organism/gram combinations.
     * Returns: { allowed: bool, reason?: string }
     */
    async validateScope(organism, gram) {
        try {
            const response = await axios.post(`${API_URL}/beta-lactam/validate-scope`, {
                organism,
                gram
            });
            return response.data;
        } catch (error) {
            console.error('Scope validation failed:', error);
            throw error;
        }
    },

    /**
     * Main CDSS engine call.
     *
     * Returns:
     *   spectrum: { Gen1: { probability, traffic_light }, Gen2: ..., ... }
     *   risk_group: "High" | "Moderate" | "Low"
     *   top_generation_recommendation: "Gen1"
     *   predicted_success_probability: 0.85
     *   ood_warning: false
     *   recommendations: [ { generation, probability, score, stewardship_note, traffic_light } ]
     *   metadata: { model_version, evidence_version, features_used }
     *   warnings: string[]
     *
     * Throws GOVERNANCE_LOCK error if AST is available (backend returns 403).
     */
    async evaluateCase(inputs, astAvailable = false) {
        try {
            const response = await axios.post(`${API_URL}/beta-lactam/evaluate`, {
                inputs,
                ast_available: astAvailable
            });
            return response.data;
        } catch (error) {
            if (error.response?.status === 403) {
                throw new Error(
                    'GOVERNANCE LOCK: Empiric prediction disabled — AST results are available.'
                );
            }
            throw error;
        }
    },

    /**
     * Log a clinician override or acceptance decision.
     * A reason_code is mandatory if decision = 'OVERRIDE'.
     */
    async logDecision(auditData) {
        // auditData = {
        //   encounter_id, user_id, model_version,
        //   generation_recommended, decision, reason_code, selected_generation
        // }
        return axios.post(`${API_URL}/beta-lactam/override`, auditData);
    },

    /**
     * Post-AST confirmatory stewardship review.
     * Returns de-escalation / maintain / escalate recommendation.
     */
    async getPostASTReview(empiricGeneration, astPanel) {
        const response = await axios.post(`${API_URL}/beta-lactam/post-ast-review`, {
            empiric_generation: empiricGeneration,
            ast_panel: astPanel
        });
        return response.data;
    },

    /**
     * Fetch governance audit trail for the Audit Log view.
     * Returns last 100 beta-lactam predictions with spectrum summaries.
     */
    async getAuditLogs() {
        const response = await axios.get(`${API_URL}/beta-lactam/audit-logs`);
        return response.data;
    },

    /**
     * Fetch confirmed lab results for a given encounter (Post-AST Review screen).
     * Returns: { results: { drug: "S/I/R" }, by_generation: { Gen1: {}, ... } }
     */
    async getLabResults(encounterId) {
        const response = await axios.get(`${API_URL}/beta-lactam/lab-results/${encounterId}`);
        return response.data;
    },

    /**
     * Fetch dynamic dropdown options (ward list, sample type list) from master data.
     * Returns [] gracefully on failure so form still renders with hardcoded fallbacks.
     */
    async getMasterDefinitions(category) {
        // category: 'WARD' or 'SAMPLE_TYPE'
        try {
            const response = await axios.get(`${API_URL}/master/definitions/${category}`);
            return response.data;
        } catch (error) {
            console.warn(`Master data fetch failed for ${category}:`, error.message);
            return [];
        }
    },

    // ── Helper utilities used by frontend components ──────────────────────────

    /**
     * Map a traffic light to a Tailwind CSS color set.
     * Returns { bg, text, border, badge } CSS classes.
     */
    getTrafficLightColors(trafficLight) {
        switch (trafficLight) {
            case 'Green':
                return {
                    bg: 'bg-green-50',
                    text: 'text-green-800',
                    border: 'border-green-200',
                    badge: 'bg-green-100 text-green-800',
                    dot: 'bg-green-500',
                };
            case 'Amber':
                return {
                    bg: 'bg-amber-50',
                    text: 'text-amber-800',
                    border: 'border-amber-200',
                    badge: 'bg-amber-100 text-amber-800',
                    dot: 'bg-amber-500',
                };
            case 'Red':
            default:
                return {
                    bg: 'bg-red-50',
                    text: 'text-red-800',
                    border: 'border-red-200',
                    badge: 'bg-red-100 text-red-800',
                    dot: 'bg-red-500',
                };
        }
    },

    /**
     * Human-readable label for each generation key.
     */
    getGenerationLabel(generationKey) {
        const labels = {
            Gen1: '1st Generation Cephalosporins',
            Gen2: '2nd Generation Cephalosporins',
            Gen3: '3rd Generation Cephalosporins',
            Gen4: '4th Generation Cephalosporins',
            Carbapenem: 'Carbapenems (Reserve)',
            BL_Combo: 'Beta-Lactam + Inhibitor',
            Non_BL: 'Non-Beta-Lactam',
        };
        return labels[generationKey] || generationKey;
    },

    /**
     * Example drugs for each generation (for tooltip / display purposes).
     */
    getGenerationExamples(generationKey) {
        const examples = {
            Gen1: 'Cefalexin, Cefazolin',
            Gen2: 'Cefuroxime, Cefaclor',
            Gen3: 'Ceftriaxone, Ceftazidime, Cefotaxime',
            Gen4: 'Cefepime',
            Carbapenem: 'Meropenem, Imipenem, Ertapenem',
            BL_Combo: 'Pip-Tazo (TZP), Amoxiclav',
            Non_BL: 'Amikacin, Ciprofloxacin, Cotrimoxazole',
        };
        return examples[generationKey] || '';
    },
};
