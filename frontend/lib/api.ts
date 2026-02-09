/**
 * API client for Merton backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface CompanyInfo {
  ticker: string;
  company_name: string;
  sector: string;
  industry: string;
}

export interface MertonOutputs {
  V: number;
  sigma_V: number;
  leverage: number;
  distance_to_default: number;
  default_probability: number;
  theo_spread_bps: number;
  solver_method: string;
}

export interface SignalOutput {
  signal: string;
  signal_strength: string;
  spread_diff_bps: number;
}

export interface AnalysisResponse {
  company: CompanyInfo;
  E: number;
  D: number;
  sigma_E: number;
  r: number;
  T: number;
  merton: MertonOutputs;
  estimated_rating: string;
  market_spread_bps: number;
  signal: SignalOutput;
  timestamp: string;
  volatility_source: string;
  has_options: boolean;
}

export interface SensitivityResponse {
  is_robust: boolean;
  base_signal: string;
  base_spread_diff: number;
  spread_std: number;
  spread_range: number;
  volatility_sensitivity: Array<{
    shock_pct: number;
    sigma_E: number;
    theo_spread_bps: number;
    spread_change_bps: number;
  }>;
  debt_sensitivity: Array<any>;
  stress_test: Array<any>;
}

export interface BatchAnalysisResponse {
  total: number;
  successes: number;
  failures: number;
  results: AnalysisResponse[];
  top_long_signals: AnalysisResponse[];
  top_short_signals: AnalysisResponse[];
}

// API functions
export const analyzeTicker = async (ticker: string): Promise<AnalysisResponse> => {
  const response = await api.post('/analyze', { ticker });
  return response.data;
};

export const analyzeSensitivity = async (ticker: string): Promise<SensitivityResponse> => {
  const response = await api.post('/analyze/sensitivity', { ticker });
  return response.data;
};

export const analyzeBatch = async (tickers: string[]): Promise<BatchAnalysisResponse> => {
  const response = await api.post('/analyze/batch', { tickers });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;