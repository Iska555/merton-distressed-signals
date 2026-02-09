"""
FastAPI route definitions
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime
import traceback

from .models import (
    AnalyzeRequest,
    BatchAnalyzeRequest,
    AnalysisResponse,
    BatchAnalysisResponse,
    SensitivityResponse,
    HealthResponse,
    ErrorResponse,
    CompanyInfo,
    MertonOutputs,
    SignalOutput
)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signals.generator import SignalGenerator
from signals.sensitivity import SensitivityAnalyzer

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_ticker(request: AnalyzeRequest):
    """
    Analyze a single ticker
    
    Returns complete Merton analysis with trading signal
    """
    try:
        ticker = request.ticker.upper()
        
        # Run analysis
        generator = SignalGenerator()
        result = generator.analyze_single(ticker, verbose=False)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Format response
        response = AnalysisResponse(
            company=CompanyInfo(
                ticker=result['ticker'],
                company_name=result['company_name'],
                sector=result['sector'],
                industry=result['industry']
            ),
            E=result['E'],
            D=result['D'],
            sigma_E=result['sigma_E'],
            r=result['r'],
            T=result['T'],
            merton=MertonOutputs(
                V=result['V'],
                sigma_V=result['sigma_V'],
                leverage=result['leverage'],
                distance_to_default=result['distance_to_default'],
                default_probability=result['default_probability'],
                theo_spread_bps=result['theo_spread_bps'],
                solver_method=result['solver_method']
            ),
            estimated_rating=result['estimated_rating'],
            market_spread_bps=result['market_spread_bps'],
            signal=SignalOutput(
                signal=result['signal'],
                signal_strength=result['signal_strength'],
                spread_diff_bps=result['spread_diff_bps']
            ),
            timestamp=result['timestamp'],
            volatility_source=result['volatility_source'],
            has_options=result['has_options']
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze/sensitivity", response_model=SensitivityResponse)
async def analyze_sensitivity(request: AnalyzeRequest):
    """
    Run sensitivity analysis on a ticker
    
    Returns robustness check and stress test results
    """
    try:
        ticker = request.ticker.upper()
        
        # Get base analysis
        generator = SignalGenerator()
        result = generator.analyze_single(ticker, verbose=False)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Run sensitivity analysis
        base_inputs = {
            'E': result['E'],
            'D': result['D'],
            'sigma_E': result['sigma_E'],
            'r': result['r'],
            'T': result['T']
        }
        
        analyzer = SensitivityAnalyzer(base_inputs)
        report = analyzer.generate_full_report(
            result['market_spread_bps'],
            ticker=ticker
        )
        
        # Format response
        response = SensitivityResponse(
            is_robust=report['robustness_check']['is_robust'],
            base_signal=report['robustness_check']['base_signal'],
            base_spread_diff=report['robustness_check']['base_spread_diff'],
            spread_std=report['robustness_check']['spread_std'],
            spread_range=report['robustness_check']['spread_range'],
            volatility_sensitivity=report['volatility_sensitivity'].to_dict('records'),
            debt_sensitivity=report['debt_sensitivity'].to_dict('records'),
            stress_test=report['stress_test'].to_dict('records')
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sensitivity analysis failed: {str(e)}"
        )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple tickers
    
    Returns ranked signals with top opportunities
    """
    try:
        tickers = [t.upper() for t in request.tickers]
        
        # Run batch analysis
        generator = SignalGenerator()
        df = generator.analyze_batch(tickers, verbose=False)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="All tickers failed")
        
        # Get top signals
        top_signals = generator.get_top_signals(df, n=10)
        
        # Format results
        results = []
        for _, row in df.iterrows():
            results.append(AnalysisResponse(
                company=CompanyInfo(
                    ticker=row['ticker'],
                    company_name=row['company_name'],
                    sector=row['sector'],
                    industry=row['industry']
                ),
                E=row['E'],
                D=row['D'],
                sigma_E=row['sigma_E'],
                r=row['r'],
                T=row['T'],
                merton=MertonOutputs(
                    V=row['V'],
                    sigma_V=row['sigma_V'],
                    leverage=row['leverage'],
                    distance_to_default=row['distance_to_default'],
                    default_probability=row['default_probability'],
                    theo_spread_bps=row['theo_spread_bps'],
                    solver_method=row['solver_method']
                ),
                estimated_rating=row['estimated_rating'],
                market_spread_bps=row['market_spread_bps'],
                signal=SignalOutput(
                    signal=row['signal'],
                    signal_strength=row['signal_strength'],
                    spread_diff_bps=row['spread_diff_bps']
                ),
                timestamp=row['timestamp'],
                volatility_source=row['volatility_source'],
                has_options=row['has_options']
            ))
        
        # Format top signals
        top_long = []
        for _, row in top_signals['long'].iterrows():
            top_long.append(AnalysisResponse(**_row_to_response(row)))
        
        top_short = []
        for _, row in top_signals['short'].iterrows():
            top_short.append(AnalysisResponse(**_row_to_response(row)))
        
        response = BatchAnalysisResponse(
            total=len(tickers),
            successes=len(results),
            failures=len(tickers) - len(results),
            results=results,
            top_long_signals=top_long,
            top_short_signals=top_short
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


def _row_to_response(row):
    """Helper to convert DataFrame row to response dict"""
    return {
        'company': CompanyInfo(
            ticker=row['ticker'],
            company_name=row['company_name'],
            sector=row['sector'],
            industry=row['industry']
        ),
        'E': row['E'],
        'D': row['D'],
        'sigma_E': row['sigma_E'],
        'r': row['r'],
        'T': row['T'],
        'merton': MertonOutputs(
            V=row['V'],
            sigma_V=row['sigma_V'],
            leverage=row['leverage'],
            distance_to_default=row['distance_to_default'],
            default_probability=row['default_probability'],
            theo_spread_bps=row['theo_spread_bps'],
            solver_method=row['solver_method']
        ),
        'estimated_rating': row['estimated_rating'],
        'market_spread_bps': row['market_spread_bps'],
        'signal': SignalOutput(
            signal=row['signal'],
            signal_strength=row['signal_strength'],
            spread_diff_bps=row['spread_diff_bps']
        ),
        'timestamp': row['timestamp'],
        'volatility_source': row['volatility_source'],
        'has_options': row['has_options']
    }