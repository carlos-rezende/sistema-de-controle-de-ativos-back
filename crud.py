from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta

from models import Ativo, Cotacao, Dividendo, Carteira, CarteiraAtivo, Transacao, IndicadorFinanceiro
import schemas

# CRUD para Ativos
def get_ativo(db: Session, ativo_id: int):
    return db.query(Ativo).filter(Ativo.id == ativo_id).first()

def get_ativo_by_ticker(db: Session, ticker: str):
    return db.query(Ativo).filter(Ativo.ticker == ticker).first()

def get_ativos(db: Session, skip: int = 0, limit: int = 100, tipo: Optional[str] = None):
    query = db.query(Ativo)
    if tipo:
        query = query.filter(Ativo.tipo == tipo)
    return query.filter(Ativo.ativo == True).offset(skip).limit(limit).all()

def create_ativo(db: Session, ativo: schemas.AtivoCreate):
    db_ativo = Ativo(**ativo.dict())
    db.add(db_ativo)
    db.commit()
    db.refresh(db_ativo)
    return db_ativo

def update_ativo(db: Session, ativo_id: int, ativo_update: schemas.AtivoUpdate):
    db_ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if db_ativo:
        update_data = ativo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_ativo, field, value)
        db_ativo.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(db_ativo)
    return db_ativo

def delete_ativo(db: Session, ativo_id: int):
    db_ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if db_ativo:
        db_ativo.ativo = False
        db.commit()
    return db_ativo

# CRUD para Cotações
def get_cotacoes(db: Session, ativo_id: int, skip: int = 0, limit: int = 100):
    return db.query(Cotacao).filter(Cotacao.ativo_id == ativo_id)\
        .order_by(desc(Cotacao.data_hora)).offset(skip).limit(limit).all()

def get_ultima_cotacao(db: Session, ativo_id: int):
    return db.query(Cotacao).filter(Cotacao.ativo_id == ativo_id)\
        .order_by(desc(Cotacao.data_hora)).first()

def get_cotacoes_periodo(db: Session, ativo_id: int, data_inicio: datetime, data_fim: datetime):
    return db.query(Cotacao).filter(
        and_(
            Cotacao.ativo_id == ativo_id,
            Cotacao.data_hora >= data_inicio,
            Cotacao.data_hora <= data_fim
        )
    ).order_by(Cotacao.data_hora).all()

def create_cotacao(db: Session, cotacao: schemas.CotacaoCreate):
    db_cotacao = Cotacao(**cotacao.dict())
    db.add(db_cotacao)
    db.commit()
    db.refresh(db_cotacao)
    return db_cotacao

def create_cotacoes_bulk(db: Session, cotacoes: List[schemas.CotacaoCreate]):
    db_cotacoes = [Cotacao(**cotacao.dict()) for cotacao in cotacoes]
    db.add_all(db_cotacoes)
    db.commit()
    return db_cotacoes

# CRUD para Dividendos
def get_dividendos(db: Session, ativo_id: int, skip: int = 0, limit: int = 100):
    return db.query(Dividendo).filter(Dividendo.ativo_id == ativo_id)\
        .order_by(desc(Dividendo.data_ex)).offset(skip).limit(limit).all()

def get_dividendos_periodo(db: Session, ativo_id: int, data_inicio: datetime, data_fim: datetime):
    return db.query(Dividendo).filter(
        and_(
            Dividendo.ativo_id == ativo_id,
            Dividendo.data_ex >= data_inicio,
            Dividendo.data_ex <= data_fim
        )
    ).order_by(Dividendo.data_ex).all()

def create_dividendo(db: Session, dividendo: schemas.DividendoCreate):
    db_dividendo = Dividendo(**dividendo.dict())
    db.add(db_dividendo)
    db.commit()
    db.refresh(db_dividendo)
    return db_dividendo

def create_dividendos_bulk(db: Session, dividendos: List[schemas.DividendoCreate]):
    db_dividendos = [Dividendo(**dividendo.dict()) for dividendo in dividendos]
    db.add_all(db_dividendos)
    db.commit()
    return db_dividendos

# CRUD para Carteiras
def get_carteira(db: Session, carteira_id: int):
    return db.query(Carteira).filter(Carteira.id == carteira_id).first()

def get_carteiras(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Carteira).filter(Carteira.ativa == True).offset(skip).limit(limit).all()

def create_carteira(db: Session, carteira: schemas.CarteiraCreate):
    db_carteira = Carteira(**carteira.dict())
    db.add(db_carteira)
    db.commit()
    db.refresh(db_carteira)
    return db_carteira

def update_carteira(db: Session, carteira_id: int, carteira_update: schemas.CarteiraUpdate):
    db_carteira = db.query(Carteira).filter(Carteira.id == carteira_id).first()
    if db_carteira:
        update_data = carteira_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_carteira, field, value)
        db_carteira.atualizada_em = datetime.utcnow()
        db.commit()
        db.refresh(db_carteira)
    return db_carteira

def delete_carteira(db: Session, carteira_id: int):
    db_carteira = db.query(Carteira).filter(Carteira.id == carteira_id).first()
    if db_carteira:
        db_carteira.ativa = False
        db.commit()
    return db_carteira

# CRUD para CarteiraAtivo
def get_carteira_ativos(db: Session, carteira_id: int):
    return db.query(CarteiraAtivo).filter(CarteiraAtivo.carteira_id == carteira_id).all()

def get_carteira_ativo(db: Session, carteira_id: int, ativo_id: int):
    return db.query(CarteiraAtivo).filter(
        and_(CarteiraAtivo.carteira_id == carteira_id, CarteiraAtivo.ativo_id == ativo_id)
    ).first()

def create_carteira_ativo(db: Session, carteira_ativo: schemas.CarteiraAtivoCreate):
    db_carteira_ativo = CarteiraAtivo(**carteira_ativo.dict())
    db.add(db_carteira_ativo)
    db.commit()
    db.refresh(db_carteira_ativo)
    return db_carteira_ativo

def update_carteira_ativo(db: Session, carteira_ativo_id: int, carteira_ativo_update: schemas.CarteiraAtivoUpdate):
    db_carteira_ativo = db.query(CarteiraAtivo).filter(CarteiraAtivo.id == carteira_ativo_id).first()
    if db_carteira_ativo:
        update_data = carteira_ativo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_carteira_ativo, field, value)
        db_carteira_ativo.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(db_carteira_ativo)
    return db_carteira_ativo

def delete_carteira_ativo(db: Session, carteira_ativo_id: int):
    db_carteira_ativo = db.query(CarteiraAtivo).filter(CarteiraAtivo.id == carteira_ativo_id).first()
    if db_carteira_ativo:
        db.delete(db_carteira_ativo)
        db.commit()
    return True

# CRUD para Transações
def get_transacoes(db: Session, carteira_id: int = None, ativo_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(Transacao)
    if carteira_id:
        query = query.filter(Transacao.carteira_id == carteira_id)
    if ativo_id:
        query = query.filter(Transacao.ativo_id == ativo_id)
    return query.order_by(desc(Transacao.data_transacao)).offset(skip).limit(limit).all()

def create_transacao(db: Session, transacao: schemas.TransacaoCreate):
    db_transacao = Transacao(**transacao.dict())
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

# CRUD para Indicadores Financeiros
def get_indicadores_financeiros(db: Session, ativo_id: int, skip: int = 0, limit: int = 100):
    return db.query(IndicadorFinanceiro).filter(IndicadorFinanceiro.ativo_id == ativo_id)\
        .order_by(desc(IndicadorFinanceiro.data_referencia)).offset(skip).limit(limit).all()

def get_ultimo_indicador_financeiro(db: Session, ativo_id: int):
    return db.query(IndicadorFinanceiro).filter(IndicadorFinanceiro.ativo_id == ativo_id)\
        .order_by(desc(IndicadorFinanceiro.data_referencia)).first()

def create_indicador_financeiro(db: Session, indicador: schemas.IndicadorFinanceiroCreate):
    db_indicador = IndicadorFinanceiro(**indicador.dict())
    db.add(db_indicador)
    db.commit()
    db.refresh(db_indicador)
    return db_indicador

# Funções auxiliares
def atualizar_valor_carteira(db: Session, carteira_id: int):
    """Atualiza o valor total da carteira baseado nos ativos"""
    carteira_ativos = get_carteira_ativos(db, carteira_id)
    valor_total = 0.0
    
    for carteira_ativo in carteira_ativos:
        ultima_cotacao = get_ultima_cotacao(db, carteira_ativo.ativo_id)
        if ultima_cotacao:
            valor_atual = carteira_ativo.quantidade * ultima_cotacao.preco_fechamento
            carteira_ativo.valor_atual = valor_atual
            valor_total += valor_atual
    
    # Atualiza o valor total da carteira
    carteira = get_carteira(db, carteira_id)
    if carteira:
        carteira.valor_total = valor_total
        carteira.atualizada_em = datetime.utcnow()
        db.commit()
    
    return valor_total

def calcular_percentual_carteira(db: Session, carteira_id: int):
    """Calcula o percentual de cada ativo na carteira"""
    carteira = get_carteira(db, carteira_id)
    if not carteira or carteira.valor_total == 0:
        return
    
    carteira_ativos = get_carteira_ativos(db, carteira_id)
    
    for carteira_ativo in carteira_ativos:
        if carteira_ativo.valor_atual:
            percentual = (carteira_ativo.valor_atual / carteira.valor_total) * 100
            carteira_ativo.percentual_carteira = percentual
    
    db.commit()

def buscar_ativos_com_ultima_cotacao(db: Session, tickers: List[str] = None):
    """Busca ativos com suas últimas cotações"""
    query = db.query(Ativo)
    if tickers:
        query = query.filter(Ativo.ticker.in_(tickers))
    
    ativos = query.filter(Ativo.ativo == True).all()
    
    result = []
    for ativo in ativos:
        ultima_cotacao = get_ultima_cotacao(db, ativo.id)
        dividendos_recentes = get_dividendos(db, ativo.id, limit=5)
        
        ativo_data = {
            "ativo": ativo,
            "ultima_cotacao": ultima_cotacao,
            "dividendos_recentes": dividendos_recentes
        }
        result.append(ativo_data)
    
    return result

