from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Ativo(Base):
    """Modelo para representar um ativo financeiro (ação, FII, etc.)"""
    __tablename__ = "ativos"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    nome_curto = Column(String(100), nullable=False)
    nome_longo = Column(String(200))
    tipo = Column(String(20), nullable=False)  # ACAO, FII, ETF, BDR, INDICE
    setor = Column(String(100))
    subsetor = Column(String(100))
    moeda = Column(String(3), default="BRL")
    logo_url = Column(String(500))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cotacoes = relationship("Cotacao", back_populates="ativo")
    dividendos = relationship("Dividendo", back_populates="ativo")
    carteiras = relationship("CarteiraAtivo", back_populates="ativo")

class Cotacao(Base):
    """Modelo para armazenar cotações dos ativos"""
    __tablename__ = "cotacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False, index=True)
    preco_abertura = Column(Float)
    preco_maximo = Column(Float)
    preco_minimo = Column(Float)
    preco_fechamento = Column(Float, nullable=False)
    volume = Column(Integer)
    variacao = Column(Float)
    variacao_percentual = Column(Float)
    valor_mercado = Column(Float)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    ativo = relationship("Ativo", back_populates="cotacoes")

class Dividendo(Base):
    """Modelo para armazenar informações de dividendos"""
    __tablename__ = "dividendos"
    
    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # DIVIDENDO, JCP, BONIFICACAO
    valor = Column(Float, nullable=False)
    data_com = Column(DateTime)  # Data com direito
    data_ex = Column(DateTime)   # Data ex-dividendo
    data_pagamento = Column(DateTime)  # Data de pagamento
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    ativo = relationship("Ativo", back_populates="dividendos")

class Carteira(Base):
    """Modelo para representar uma carteira de investimentos"""
    __tablename__ = "carteiras"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    valor_total = Column(Float, default=0.0)
    ativa = Column(Boolean, default=True)
    criada_em = Column(DateTime, default=datetime.utcnow)
    atualizada_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    ativos = relationship("CarteiraAtivo", back_populates="carteira")

class CarteiraAtivo(Base):
    """Modelo para representar a relação entre carteira e ativos"""
    __tablename__ = "carteira_ativos"
    
    id = Column(Integer, primary_key=True, index=True)
    carteira_id = Column(Integer, ForeignKey("carteiras.id"), nullable=False)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    quantidade = Column(Float, nullable=False)
    preco_medio = Column(Float, nullable=False)
    valor_investido = Column(Float, nullable=False)
    valor_atual = Column(Float)
    percentual_carteira = Column(Float)
    adicionado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    carteira = relationship("Carteira", back_populates="ativos")
    ativo = relationship("Ativo", back_populates="carteiras")

class Transacao(Base):
    """Modelo para registrar transações de compra/venda"""
    __tablename__ = "transacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    carteira_id = Column(Integer, ForeignKey("carteiras.id"), nullable=False)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    tipo = Column(String(10), nullable=False)  # COMPRA, VENDA
    quantidade = Column(Float, nullable=False)
    preco = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)
    taxa_corretagem = Column(Float, default=0.0)
    data_transacao = Column(DateTime, nullable=False)
    observacoes = Column(Text)
    criada_em = Column(DateTime, default=datetime.utcnow)

class IndicadorFinanceiro(Base):
    """Modelo para armazenar indicadores financeiros dos ativos"""
    __tablename__ = "indicadores_financeiros"
    
    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    data_referencia = Column(DateTime, nullable=False)
    
    # Indicadores de valuation
    preco_lucro = Column(Float)  # P/L
    preco_vp = Column(Float)     # P/VP
    preco_vendas = Column(Float) # P/Vendas
    ev_ebitda = Column(Float)    # EV/EBITDA
    dividend_yield = Column(Float)
    
    # Indicadores de rentabilidade
    roe = Column(Float)          # Return on Equity
    roa = Column(Float)          # Return on Assets
    roic = Column(Float)         # Return on Invested Capital
    margem_bruta = Column(Float)
    margem_liquida = Column(Float)
    
    # Indicadores de endividamento
    divida_liquida_pl = Column(Float)
    divida_liquida_ebitda = Column(Float)
    
    # Específicos para FIIs
    p_vp_fii = Column(Float)     # P/VP para FIIs
    dividend_yield_fii = Column(Float)
    vacancia = Column(Float)     # Taxa de vacância
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    ativo = relationship("Ativo")

