"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalyzeRequest(BaseModel):
    """Request model for single ticker analysis"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    include_sensitivity: bool = Field(default=False, description="Include sensitivity analysis")


class BatchAnalyzeRequest(BaseModel):
    """Request model for batch analysis"""
    tickers: List[str] = Field(..., min_items=1, max_items=50, description="List of tickers")
    include_sensitivity: bool = Field(default=False)


class CompanyInfo(BaseModel):
    """Company metadata"""
    ticker: str
    company_name: str
    sector: str
    industry: str


class MertonOutputs(BaseModel):
    """Merton model outputs"""
    V: float = Field(..., description="Asset value")
    sigma_V: float = Field(..., description="Asset volatility")
    leverage: float = Field(..., description="Debt to asset ratio")
    distance_to_default: float = Field(..., description="Distance to default in sigmas")
    default_probability: float = Field(..., description="Probability of default")
    theo_spread_bps: float = Field(..., description="Theoretical credit spread in bps")
    solver_method: str


class SignalOutput(BaseModel):
    """Trading signal"""
    signal: str = Field(..., description="LONG CREDIT | SHORT CREDIT | NEUTRAL")
    signal_strength: str = Field(..., description="Star rating")
    spread_diff_bps: float = Field(..., description="Theoretical - Market spread")


class AnalysisResponse(BaseModel):
    """Response model for single ticker analysis"""
    # Company info
    company: CompanyInfo
    
    # Inputs
    E: float = Field(..., description="Market cap")
    D: float = Field(..., description="Total debt")
    sigma_E: float = Field(..., description="Equity volatility")
    r: float
    T: float
    
    # Merton outputs
    merton: MertonOutputs
    
    # Market data
    estimated_rating: str
    market_spread_bps: float
    
    # Signal
    signal: SignalOutput
    
    # Metadata
    timestamp: str
    volatility_source: str
    has_options: bool


class SensitivityResponse(BaseModel):
    """Sensitivity analysis response"""
    is_robust: bool
    base_signal: str
    base_spread_diff: float
    spread_std: float
    spread_range: float
    volatility_sensitivity: List[Dict[str, Any]]
    debt_sensitivity: List[Dict[str, Any]]
    stress_test: List[Dict[str, Any]]


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis"""
    total: int
    successes: int
    failures: int
    results: List[AnalysisResponse]
    top_long_signals: List[AnalysisResponse]
    top_short_signals: List[AnalysisResponse]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    ticker: Optional[str] = None