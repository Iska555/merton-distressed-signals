/**
 * API client for Merton backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // ── UPGRADED: 120 seconds for heavy compute loads
  headers: { 'Content-Type': 'application/json' },
});

// ── Existing types ─────────────────────────────────────────────────

export interface CompanyInfo {
  ticker:       string;
  company_name: string;
  sector:       string;
  industry:     string;
}

export interface MertonOutputs {
  V:                   number;
  sigma_V:             number;
  distance_to_default: number;
  theo_spread_bps:     number;
  default_prob?:       number;
  asset_value?:        number;
  asset_volatility?:   number;
  default_probability: number;
  leverage:            number;
  solver_method:       string;
}

export interface SignalOutput {
  signal:          string;
  signal_strength: string;
  spread_diff_bps: number;
}

export interface AnalysisResponse {
  company:          CompanyInfo;
  E:                number;
  D:                number;
  sigma_E:          number;
  r:                number;
  T:                number;
  merton:           MertonOutputs;
  estimated_rating: string;
  market_spread_bps: number;
  signal:           SignalOutput;
  timestamp:        string;
  volatility_source: string;
  has_options:      boolean;
}

export interface SensitivityResponse {
  is_robust:              boolean;
  base_signal:            string;
  base_spread_diff:       number;
  spread_std:             number;
  spread_range:           number;
  volatility_sensitivity: Array<{
    shock_pct:           number;
    sigma_E:             number;
    theo_spread_bps:     number;
    spread_change_bps:   number;
  }>;
  debt_sensitivity: Array<Record<string, unknown>>;
  stress_test:      Array<Record<string, unknown>>;
}

export interface BatchAnalysisResponse {
  total:             number;
  successes:         number;
  failures:          number;
  results:           AnalysisResponse[];
  top_long_signals:  AnalysisResponse[];
  top_short_signals: AnalysisResponse[];
}

// ── Existing API functions ─────────────────────────────────────────

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

// ── Event Scanner types ────────────────────────────────────────────

export type EventSignal = 'NEUTRAL' | 'LONG_CREDIT' | 'SHORT_CREDIT' | 'CRITICAL_SHORT';
export type TriggerType = 'PRICE_MOVE' | 'VOL_SPIKE' | 'MANUAL';

export interface NewsItem {
  title:     string;
  publisher: string;
  timestamp: string;   // ISO 8601 UTC
  url:       string;
}

export interface MertonEventResult {
  ticker:                  string;
  company_name:            string;
  scan_timestamp:          string;
  share_price:             number;
  equity_value_b:          number;
  face_value_debt_b:       number;
  risk_free_rate:          number;
  equity_vol:              number;
  implied_asset_value_b:   number;
  implied_asset_vol:       number;
  distance_to_default:     number;
  default_probability_pct: number;
  theoretical_spread_bps:  number;
  market_spread_bps:       number;
  alpha_gap_bps:           number;
  signal:                  EventSignal;
  trigger_type:            TriggerType;
  price_change_pct:        number;
  vol_change_pct:          number;
  solver_converged:        boolean;
  debt_override_applied:   boolean;        // Added for Bank Structural Proxy
  recent_news:             NewsItem[];     // Added for Catalyst Wire
  error?:                  string | null;
}

export interface ScanSession {
  session_id:     string;
  scan_date:      string;
  triggered_at:   string;
  total_screened: number;
  signals_fired:  number;
  results:        MertonEventResult[];
}

export interface ScanHistoryEntry {
  session_id:     string;
  scan_date:      string;
  triggered_at:   string;
  signals_fired:  number;
  total_screened: number;
}

// ── Event Scanner API functions ────────────────────────────────────

export const getLatestScan = async (): Promise<ScanSession> => {
  const response = await api.get('/events/scan/latest');
  return response.data;
};

export const getScanHistory = async (
  days = 30,
): Promise<{ sessions: ScanHistoryEntry[]; count: number }> => {
  const response = await api.get('/events/scan/history', { params: { days } });
  return response.data;
};

export const triggerManualScan = async (
  tickers: string[],
  risk_free_rate = 0.045,
): Promise<{ status: string; tickers: string[]; count: number }> => {
  const response = await api.post('/events/scan/manual', { tickers, risk_free_rate });
  return response.data;
};

/**
 * Full SSE stream URL — use directly with EventSource (not axios).
 * Reads NEXT_PUBLIC_API_URL so it works in any environment.
 */
export const getStreamUrl = (): string =>
  `${API_BASE_URL}/events/scan/stream`;