from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

from database import get_db, init_db
from services.brapi_service import brapi_service
from routers import analytics
import crud
import schemas
import models

# Carrega variáveis de ambiente
load_dotenv()

# Cria a aplicação FastAPI
app = FastAPI(
    title="Sistema de Controle de Ativos",
    description="API para controle e análise de ativos financeiros (ações, FIIs, etc.)",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui routers
app.include_router(analytics.router)

# Inicializa o banco de dados na inicialização
@app.on_event("startup")
async def startup_event():
    init_db()

# Endpoints para Ativos
@app.get("/ativos/", response_model=List[schemas.Ativo])
def listar_ativos(
    skip: int = 0, 
    limit: int = 100, 
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista todos os ativos cadastrados"""
    ativos = crud.get_ativos(db, skip=skip, limit=limit, tipo=tipo)
    return ativos

@app.get("/ativos/{ativo_id}", response_model=schemas.Ativo)
def obter_ativo(ativo_id: int, db: Session = Depends(get_db)):
    """Obtém um ativo específico por ID"""
    ativo = crud.get_ativo(db, ativo_id=ativo_id)
    if ativo is None:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@app.get("/ativos/ticker/{ticker}", response_model=schemas.AtivoComCotacao)
def obter_ativo_por_ticker(ticker: str, db: Session = Depends(get_db)):
    """Obtém um ativo específico por ticker com última cotação"""
    ativo = crud.get_ativo_by_ticker(db, ticker=ticker.upper())
    if ativo is None:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    ultima_cotacao = crud.get_ultima_cotacao(db, ativo.id)
    dividendos_recentes = crud.get_dividendos(db, ativo.id, limit=5)
    
    return schemas.AtivoComCotacao(
        **ativo.__dict__,
        ultima_cotacao=ultima_cotacao,
        dividendos_recentes=dividendos_recentes
    )

@app.post("/ativos/", response_model=schemas.Ativo)
def criar_ativo(ativo: schemas.AtivoCreate, db: Session = Depends(get_db)):
    """Cria um novo ativo"""
    # Verifica se o ticker já existe
    db_ativo = crud.get_ativo_by_ticker(db, ticker=ativo.ticker.upper())
    if db_ativo:
        raise HTTPException(status_code=400, detail="Ticker já cadastrado")
    
    ativo.ticker = ativo.ticker.upper()
    return crud.create_ativo(db=db, ativo=ativo)

@app.put("/ativos/{ativo_id}", response_model=schemas.Ativo)
def atualizar_ativo(
    ativo_id: int, 
    ativo_update: schemas.AtivoUpdate, 
    db: Session = Depends(get_db)
):
    """Atualiza um ativo existente"""
    ativo = crud.update_ativo(db, ativo_id=ativo_id, ativo_update=ativo_update)
    if ativo is None:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@app.delete("/ativos/{ativo_id}", response_model=schemas.ResponseMessage)
def deletar_ativo(ativo_id: int, db: Session = Depends(get_db)):
    """Desativa um ativo"""
    ativo = crud.delete_ativo(db, ativo_id=ativo_id)
    if ativo is None:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return schemas.ResponseMessage(message="Ativo desativado com sucesso")

# Endpoints para buscar dados externos
@app.post("/ativos/buscar-externos/", response_model=schemas.AtualizacaoPrecos)
def buscar_dados_externos(
    request: schemas.BuscaAtivoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Busca dados de ativos da API externa (brapi.dev)"""
    
    def processar_dados_externos():
        try:
            # Busca dados da API brapi.dev
            params = {}
            if request.incluir_historico:
                params["range"] = request.range_historico
                params["interval"] = "1d"
            if request.incluir_dividendos:
                params["dividends"] = "true"
            
            data = brapi_service.get_quote(request.tickers, **params)
            
            if "error" in data:
                return
            
            processed_data = brapi_service.parse_quote_data(data)
            cotacoes_inseridas = 0
            
            for item in processed_data:
                # Verifica se o ativo existe, se não, cria
                ativo = crud.get_ativo_by_ticker(db, item["ticker"])
                if not ativo:
                    ativo_create = schemas.AtivoCreate(
                        ticker=item["ticker"],
                        nome_curto=item["nome_curto"],
                        nome_longo=item["nome_longo"],
                        tipo="ACAO",  # Assumindo ação por padrão
                        moeda=item["moeda"],
                        logo_url=item["logo_url"]
                    )
                    ativo = crud.create_ativo(db, ativo_create)
                
                # Insere cotação atual
                cotacao_create = schemas.CotacaoCreate(
                    ativo_id=ativo.id,
                    data_hora=item["data_hora"],
                    preco_abertura=item["preco_abertura"],
                    preco_maximo=item["preco_maximo"],
                    preco_minimo=item["preco_minimo"],
                    preco_fechamento=item["preco_fechamento"],
                    volume=item["volume"],
                    variacao=item["variacao"],
                    variacao_percentual=item["variacao_percentual"],
                    valor_mercado=item["valor_mercado"]
                )
                crud.create_cotacao(db, cotacao_create)
                cotacoes_inseridas += 1
                
                # Insere dados históricos se disponíveis
                if "historico" in item:
                    cotacoes_historicas = []
                    for hist in item["historico"]:
                        cotacao_hist = schemas.CotacaoCreate(
                            ativo_id=ativo.id,
                            data_hora=hist["data"],
                            preco_abertura=hist["abertura"],
                            preco_maximo=hist["maximo"],
                            preco_minimo=hist["minimo"],
                            preco_fechamento=hist["fechamento"],
                            volume=hist["volume"]
                        )
                        cotacoes_historicas.append(cotacao_hist)
                    
                    if cotacoes_historicas:
                        crud.create_cotacoes_bulk(db, cotacoes_historicas)
                        cotacoes_inseridas += len(cotacoes_historicas)
                
                # Insere dividendos se disponíveis
                if "dividendos" in item:
                    dividendos = []
                    for div in item["dividendos"]:
                        dividendo = schemas.DividendoCreate(
                            ativo_id=ativo.id,
                            tipo=div["tipo"],
                            valor=div["valor"],
                            data_com=div["data_com"],
                            data_ex=div["data_ex"],
                            data_pagamento=div["data_pagamento"]
                        )
                        dividendos.append(dividendo)
                    
                    if dividendos:
                        crud.create_dividendos_bulk(db, dividendos)
            
        except Exception as e:
            print(f"Erro ao processar dados externos: {e}")
    
    # Executa o processamento em background
    background_tasks.add_task(processar_dados_externos)
    
    return schemas.AtualizacaoPrecos(
        tickers_atualizados=request.tickers,
        total_cotacoes=0,  # Será atualizado em background
        sucesso=True,
        mensagem="Processamento iniciado em background"
    )

# Endpoints para Cotações
@app.get("/ativos/{ativo_id}/cotacoes/", response_model=List[schemas.Cotacao])
def listar_cotacoes(
    ativo_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Lista cotações de um ativo"""
    cotacoes = crud.get_cotacoes(db, ativo_id=ativo_id, skip=skip, limit=limit)
    return cotacoes

@app.get("/ativos/{ativo_id}/cotacoes/ultima/", response_model=schemas.Cotacao)
def obter_ultima_cotacao(ativo_id: int, db: Session = Depends(get_db)):
    """Obtém a última cotação de um ativo"""
    cotacao = crud.get_ultima_cotacao(db, ativo_id=ativo_id)
    if cotacao is None:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    return cotacao

# Endpoints para Dividendos
@app.get("/ativos/{ativo_id}/dividendos/", response_model=List[schemas.Dividendo])
def listar_dividendos(
    ativo_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Lista dividendos de um ativo"""
    dividendos = crud.get_dividendos(db, ativo_id=ativo_id, skip=skip, limit=limit)
    return dividendos

# Endpoints para Carteiras
@app.get("/carteiras/", response_model=List[schemas.Carteira])
def listar_carteiras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todas as carteiras"""
    carteiras = crud.get_carteiras(db, skip=skip, limit=limit)
    return carteiras

@app.get("/carteiras/{carteira_id}", response_model=schemas.CarteiraDetalhada)
def obter_carteira(carteira_id: int, db: Session = Depends(get_db)):
    """Obtém uma carteira específica com detalhes"""
    carteira = crud.get_carteira(db, carteira_id=carteira_id)
    if carteira is None:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    # Atualiza valores da carteira
    crud.atualizar_valor_carteira(db, carteira_id)
    crud.calcular_percentual_carteira(db, carteira_id)
    
    # Busca ativos da carteira
    carteira_ativos = crud.get_carteira_ativos(db, carteira_id)
    
    # Calcula métricas
    total_investido = sum(ca.valor_investido for ca in carteira_ativos)
    total_atual = sum(ca.valor_atual or 0 for ca in carteira_ativos)
    rentabilidade = total_atual - total_investido
    rentabilidade_percentual = (rentabilidade / total_investido * 100) if total_investido > 0 else 0
    
    return schemas.CarteiraDetalhada(
        **carteira.__dict__,
        ativos=carteira_ativos,
        total_investido=total_investido,
        total_atual=total_atual,
        rentabilidade=rentabilidade,
        rentabilidade_percentual=rentabilidade_percentual
    )

@app.post("/carteiras/", response_model=schemas.Carteira)
def criar_carteira(carteira: schemas.CarteiraCreate, db: Session = Depends(get_db)):
    """Cria uma nova carteira"""
    return crud.create_carteira(db=db, carteira=carteira)

@app.put("/carteiras/{carteira_id}", response_model=schemas.Carteira)
def atualizar_carteira(
    carteira_id: int, 
    carteira_update: schemas.CarteiraUpdate, 
    db: Session = Depends(get_db)
):
    """Atualiza uma carteira existente"""
    carteira = crud.update_carteira(db, carteira_id=carteira_id, carteira_update=carteira_update)
    if carteira is None:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    return carteira

# Endpoints para adicionar ativos à carteira
@app.post("/carteiras/{carteira_id}/ativos/", response_model=schemas.CarteiraAtivo)
def adicionar_ativo_carteira(
    carteira_id: int,
    carteira_ativo: schemas.CarteiraAtivoCreate,
    db: Session = Depends(get_db)
):
    """Adiciona um ativo à carteira"""
    # Verifica se a carteira existe
    carteira = crud.get_carteira(db, carteira_id)
    if not carteira:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    # Verifica se o ativo existe
    ativo = crud.get_ativo(db, carteira_ativo.ativo_id)
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    # Verifica se o ativo já está na carteira
    existing = crud.get_carteira_ativo(db, carteira_id, carteira_ativo.ativo_id)
    if existing:
        raise HTTPException(status_code=400, detail="Ativo já está na carteira")
    
    carteira_ativo.carteira_id = carteira_id
    return crud.create_carteira_ativo(db=db, carteira_ativo=carteira_ativo)

# Endpoints para Transações
@app.get("/transacoes/", response_model=List[schemas.Transacao])
def listar_transacoes(
    carteira_id: Optional[int] = None,
    ativo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista transações"""
    transacoes = crud.get_transacoes(
        db, carteira_id=carteira_id, ativo_id=ativo_id, skip=skip, limit=limit
    )
    return transacoes

@app.post("/transacoes/", response_model=schemas.Transacao)
def criar_transacao(transacao: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    """Cria uma nova transação"""
    return crud.create_transacao(db=db, transacao=transacao)

# Endpoint de status da API
@app.get("/")
def root():
    """Endpoint raiz da API"""
    return {
        "message": "Sistema de Controle de Ativos API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
def health_check():
    """Endpoint de verificação de saúde"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )

