from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from services.analytics_service import analytics_service
from schemas import ResponseMessage

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/ativo/{ticker}")
def analisar_ativo(
    ticker: str,
    periodo_dias: int = 252,
    db: Session = Depends(get_db)
):
    """Análise completa de um ativo"""
    resultado = analytics_service.analisar_ativo(db, ticker.upper(), periodo_dias)
    
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    
    return resultado

@router.post("/comparar-ativos")
def comparar_ativos(
    tickers: List[str],
    periodo_dias: int = 252,
    db: Session = Depends(get_db)
):
    """Compara múltiplos ativos"""
    # Converte tickers para maiúsculo
    tickers_upper = [t.upper() for t in tickers]
    
    resultado = analytics_service.comparar_ativos(db, tickers_upper, periodo_dias)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    return resultado

@router.get("/carteira/{carteira_id}")
def analisar_carteira(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """Análise completa de uma carteira"""
    resultado = analytics_service.analisar_carteira(db, carteira_id)
    
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    
    return resultado

@router.get("/carteira/{carteira_id}/relatorio")
def relatorio_carteira(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """Relatório completo da carteira com gráficos"""
    resultado = analytics_service.gerar_relatorio_carteira(db, carteira_id)
    
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    
    return resultado

@router.get("/ativo/{ticker}/grafico")
def grafico_performance(
    ticker: str,
    periodo_dias: int = 252,
    db: Session = Depends(get_db)
):
    """Gera gráfico de performance de um ativo"""
    html_grafico = analytics_service.gerar_grafico_performance(db, ticker.upper(), periodo_dias)
    
    if not html_grafico:
        raise HTTPException(status_code=404, detail="Ativo não encontrado ou dados insuficientes")
    
    return Response(content=html_grafico, media_type="text/html")

@router.get("/metricas-mercado")
def metricas_mercado(db: Session = Depends(get_db)):
    """Métricas gerais do mercado baseadas nos ativos cadastrados"""
    # Esta função pode ser expandida para incluir métricas como:
    # - Número total de ativos
    # - Setores mais representados
    # - Ativos com melhor performance
    # - etc.
    
    from crud import get_ativos
    from models import Ativo
    
    ativos = get_ativos(db, limit=1000)
    
    # Contagem por tipo
    tipos = {}
    setores = {}
    
    for ativo in ativos:
        # Contagem por tipo
        if ativo.tipo not in tipos:
            tipos[ativo.tipo] = 0
        tipos[ativo.tipo] += 1
        
        # Contagem por setor
        setor = ativo.setor or "Não classificado"
        if setor not in setores:
            setores[setor] = 0
        setores[setor] += 1
    
    return {
        "total_ativos": len(ativos),
        "distribuicao_tipos": tipos,
        "distribuicao_setores": setores,
        "ativos_recentes": [
            {
                "ticker": a.ticker,
                "nome": a.nome_curto,
                "tipo": a.tipo,
                "setor": a.setor
            } for a in ativos[:10]
        ]
    }

