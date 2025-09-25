# analytics.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

# --- Importações Corrigidas ---
from src.database import get_db
from src.services.analytics_service import AnalyticsService
from src import schemas
from src import crud

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/ativo/{ticker}",
    response_model=schemas.AnaliseAtivoResponse,
    summary="Análise de um ativo financeiro"
)
def analisar_ativo(
    ticker: str,
    periodo_dias: int = 252,
    db: Session = Depends(get_db)
):
    """
    Retorna uma análise de performance completa de um ativo financeiro.
    """
    try:
        # ✅ A CORREÇÃO: Cria uma instância do serviço e passa o 'db'
        service = AnalyticsService(db)

        # ✅ Chama o método na instância
        resultado = service.analisar_ativo(ticker.upper(), periodo_dias)

        if "error" in resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])

        return resultado

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"Erro inesperado no serviço de análise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao processar a análise do ativo."
        )


@router.post(
    "/comparar-ativos",
    response_model=schemas.ComparacaoAtivosResponse,
    summary="Compara a performance de múltiplos ativos"
)
def comparar_ativos(
    request: schemas.CompararAtivosRequest,
    db: Session = Depends(get_db)
):
    """
    Compara o desempenho e risco de múltiplos ativos.
    """
    try:
        # ✅ CORREÇÃO: Cria a instância do serviço
        service = AnalyticsService(db)

        tickers_upper = [t.upper() for t in request.tickers]

        # ✅ Chama o método na instância
        resultado = service.comparar_ativos(
            tickers_upper, request.periodo_dias)

        if "error" in resultado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])

        return resultado
    except Exception as e:
        print(f"Erro inesperado na comparação de ativos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao comparar os ativos."
        )


@router.get(
    "/carteira/{carteira_id}",
    response_model=schemas.AnaliseCarteiraResponse,
    summary="Análise de uma carteira de investimentos"
)
def analisar_carteira(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna uma análise completa de uma carteira, incluindo rentabilidade e diversificação.
    """
    # ✅ CORREÇÃO: Cria a instância do serviço
    service = AnalyticsService(db)

    # ✅ Chama o método na instância
    resultado = service.analisar_carteira(carteira_id)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])

    return resultado


@router.get(
    "/carteira/{carteira_id}/relatorio",
    summary="Relatório visual da carteira"
)
def relatorio_carteira(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna um relatório visual completo da carteira, incluindo gráficos.
    """
    # ✅ CORREÇÃO: Cria a instância do serviço
    service = AnalyticsService(db)

    # ✅ Chama o método na instância
    resultado = service.gerar_relatorio_carteira(carteira_id)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])

    return resultado


@router.get(
    "/ativo/{ticker}/grafico",
    summary="Gráfico de performance do ativo",
    response_class=Response,
    responses={
        200: {"content": {"text/html": {}}},
        404: {"description": "Ativo não encontrado ou dados insuficientes"}
    }
)
def grafico_performance(
    ticker: str,
    periodo_dias: int = 252,
    db: Session = Depends(get_db)
):
    """
    Gera um gráfico interativo com a performance e volume de um ativo.
    """
    try:
        # ✅ CORREÇÃO: Cria a instância do serviço
        service = AnalyticsService(db)

        # ✅ Chama o método na instância
        html_grafico = service.gerar_grafico_performance(
            ticker.upper(), periodo_dias)

        if not html_grafico:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Ativo não encontrado ou dados insuficientes")
        return Response(content=html_grafico, media_type="text/html")
    except Exception as e:
        print(f"Erro inesperado ao gerar gráfico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao gerar o gráfico."
        )


@router.get(
    "/metricas-mercado",
    response_model=schemas.MetricasMercadoResponse,
    summary="Métricas agregadas do mercado"
)
def metricas_mercado(db: Session = Depends(get_db)):
    # ✅ CORREÇÃO: Cria a instância do serviço
    service = AnalyticsService(db)

    # ✅ Chama o método na instância
    return service.analisar_metricas_mercado()
