import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware


from src.services import analytics_service
from src.services.brapi_service import brapi_service
from src import crud
from src.database import get_db, init_db
from src import schemas
from src.routers import analytics, wallet, ativos


app = FastAPI(
    title="API de Gestão de Ativos Financeiros",
    description="API robusta para coletar dados, gerenciar carteiras e analisar ativos financeiros.",
    version="1.0.0",
)
origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)
# Inclui os roteadores da aplicação
app.include_router(analytics.router)
app.include_router(wallet.router)
app.include_router(ativos.router)

# --- Eventos de Inicialização ---


@app.on_event("startup")
def on_startup():
    """
    Executa a inicialização do banco de dados na inicialização do servidor.
    """
    init_db()
    print("API pronta para uso.")

# --- Rotas de Saúde e Informação ---


@app.get("/", summary="Informações da API")
def read_root():
    """
    Retorna informações básicas sobre a API.
    """
    return {
        "message": "API de Gestão de Ativos Financeiros",
        "version": app.version,
        "status": "online",
    }


@app.get("/health", summary="Verificação de Saúde")
def health_check():
    """
    Verifica o status de saúde da API.
    """
    return {"status": "healthy"}

# --- Rotas de Coleta e Sincronização de Dados ---


@app.post(
    "/api/sync/quotes",
    response_model=schemas.AtualizacaoPrecos,
    status_code=status.HTTP_201_CREATED,
    summary="Sincronizar Cotações de Ativos"
)
def sync_quotes(request: schemas.BuscaAtivoRequest, db: Session = Depends(get_db)):
    """
    Sincroniza as cotações, dados históricos e de dividendos dos ativos
    especificados com a API brapi.
    """
    try:
        # Pega os dados da BrapiService
        data = brapi_service.get_quote(
            request.tickers,
            range=request.range_historico if request.incluir_historico else None,
            dividends="true" if request.incluir_dividendos else None
        )

        if not data or "results" not in data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum dado encontrado para os tickers fornecidos."
            )

        # Processa os dados brutos e os organiza para inserção no DB
        processed_data = brapi_service.parse_quote_data(data)

        tickers_atualizados = []
        total_cotacoes_inseridas = 0

        for item in processed_data:
            ticker = item.get("ticker")

            # Garante que o ticker seja uma string válida e em maiúsculas
            if not ticker or not isinstance(ticker, str):
                continue
            ticker = ticker.upper()

            # Busca o ativo no DB, ou cria um novo se não existir
            ativo_db = crud.get_ativo_by_ticker(db, ticker=ticker)
            if not ativo_db:
                ativo_create = schemas.AtivoCreate(
                    ticker=ticker,
                    nome_curto=item.get("nome_curto"),
                    nome_longo=item.get("nome_longo"),
                    tipo=schemas.TipoAtivo.ACAO,  # Supondo que sejam ações, o que pode ser melhorado
                    moeda=item.get("moeda"),
                    logo_url=item.get("logo_url")
                )
                ativo_db = crud.create_ativo(db, ativo=ativo_create)

            # Separa a cotação atual, que é um item individual
            cotacao_atual = item.get("preco_fechamento")

            if cotacao_atual:
                cotacao_create = schemas.CotacaoCreate(
                    ativo_id=ativo_db.id,
                    data_hora=item.get("data_hora"),
                    preco_fechamento=cotacao_atual,
                    preco_abertura=item.get("preco_abertura"),
                    preco_maximo=item.get("preco_maximo"),
                    preco_minimo=item.get("preco_minimo"),
                    volume=item.get("volume"),
                    variacao=item.get("variacao"),
                    variacao_percentual=item.get("variacao_percentual"),
                    valor_mercado=item.get("valor_mercado")
                )
                crud.create_cotacao(db, cotacao=cotacao_create)
                total_cotacoes_inseridas += 1

            # Insere dados históricos em massa
            historical_data = item.get("historico")
            if historical_data:
                cotacoes_para_inserir = [
                    schemas.CotacaoCreate(
                        ativo_id=ativo_db.id,
                        data_hora=h.get("data"),
                        preco_abertura=h.get("abertura"),
                        preco_maximo=h.get("maximo"),
                        preco_minimo=h.get("minimo"),
                        preco_fechamento=h.get("fechamento"),
                        volume=h.get("volume")
                    ) for h in historical_data
                ]
                crud.create_cotacoes_bulk(db, cotacoes_para_inserir)
                total_cotacoes_inseridas += len(historical_data)

            # Insere dados de dividendos em massa
            dividends_data = item.get("dividendos")
            if dividends_data:
                dividendos_para_inserir = [
                    schemas.DividendoCreate(
                        ativo_id=ativo_db.id,
                        tipo=d.get("tipo"),
                        valor=d.get("valor"),
                        data_com=d.get("data_com"),
                        data_ex=d.get("data_ex"),
                        data_pagamento=d.get("data_pagamento")
                    ) for d in dividends_data
                ]
                crud.create_dividendos_bulk(db, dividendos_para_inserir)

            tickers_atualizados.append(ticker)

        return schemas.AtualizacaoPrecos(
            tickers_atualizados=tickers_atualizados,
            total_cotacoes=total_cotacoes_inseridas,
            sucesso=True,
            mensagem="Sincronização concluída com sucesso."
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante a sincronização: {e}"
        )


# --- Rota de Análise de Ativo ---


@app.get("/api/analytics/stock/{ticker}", summary="Análise de Performance de Ativo")
def analyze_stock(ticker: str, period: int = 252, db: Session = Depends(get_db)):
    """
    Retorna uma análise de performance completa para um ativo específico.
    """
    analysis = analytics_service.analisar_ativo(db, ticker, period)
    if "error" in analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=analysis["error"]
        )
    return analysis


# --- Execução da Aplicação ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
