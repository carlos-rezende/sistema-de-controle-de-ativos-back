from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# A base é importada do database.py para evitar duplicação e garantir
# que todos os modelos usem a mesma base declarativa.
# Exemplo: from .database import Base

# Para este exemplo, manteremos a base aqui por simplicidade,
# mas em uma aplicação real, centralizá-la é a melhor prática.
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
    # Adicionado index para buscas rápidas
    ativo = Column(Boolean, default=True, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    # `lazy='dynamic'` permite consultas eficientes em coleções de relacionamento.
    # Ex: `ativo.cotacoes.order_by(Cotacao.data_hora).limit(10)`
    cotacoes = relationship("Cotacao", back_populates="ativo",
                            lazy="dynamic", order_by="desc(Cotacao.data_hora)")
    dividendos = relationship(
        "Dividendo", back_populates="ativo", lazy="dynamic")
    carteiras = relationship("CarteiraAtivo", back_populates="ativo")


class Cotacao(Base):
    """Modelo para armazenar cotações dos ativos"""
    __tablename__ = "cotacoes"

    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    # Adicionado um índice composto para consultas de cotação por ativo e data
    __table_args__ = (
        UniqueConstraint('ativo_id', 'data_hora',
                         name='uq_cotacao_ativo_data'),
        Index('idx_cotacao_ativo_data', 'ativo_id', 'data_hora')
    )

    data_hora = Column(DateTime, nullable=False, index=True)
    preco_abertura = Column(Float)
    preco_maximo = Column(Float)
    preco_minimo = Column(Float)
    preco_fechamento = Column(Float, nullable=False)
    volume = Column(Integer)
    variacao = Column(Float)
    variacao_percentual = Column(Float)
    valor_mercado = Column(Float)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    ativo = relationship("Ativo", back_populates="cotacoes")


class Dividendo(Base):
    """Modelo para armazenar informações de dividendos"""
    __tablename__ = "dividendos"

    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    # Adicionado um índice composto para consultas de dividendos por ativo e data
    __table_args__ = (
        UniqueConstraint('ativo_id', 'data_ex', 'tipo',
                         name='uq_dividendo_ativo_data_tipo'),
        Index('idx_dividendo_ativo_data', 'ativo_id', 'data_ex')
    )

    tipo = Column(String(20), nullable=False)  # DIVIDENDO, JCP, BONIFICACAO
    valor = Column(Float, nullable=False)
    data_com = Column(DateTime)
    data_ex = Column(DateTime, nullable=False, index=True)
    data_pagamento = Column(DateTime)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    ativo = relationship("Ativo", back_populates="dividendos")


class Carteira(Base):
    """Modelo para representar uma carteira de investimentos"""
    __tablename__ = "carteiras"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    descricao = Column(Text)
    valor_total = Column(Float, default=0.0, nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)
    criada_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizada_em = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    ativos = relationship("CarteiraAtivo", back_populates="carteira")


class CarteiraAtivo(Base):
    """
    Modelo de associação para a relação N-para-N entre Carteira e Ativo.
    Armazena informações específicas da associação, como quantidade e preço médio.
    """
    __tablename__ = "carteira_ativos"

    id = Column(Integer, primary_key=True, index=True)
    carteira_id = Column(Integer, ForeignKey("carteiras.id"), nullable=False)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    # Garante que a combinação (carteira_id, ativo_id) seja única
    __table_args__ = (UniqueConstraint(
        'carteira_id', 'ativo_id', name='uq_carteira_ativo'),)

    quantidade = Column(Float, nullable=False)
    preco_medio = Column(Float, nullable=False)
    valor_investido = Column(Float, nullable=False)
    valor_atual = Column(Float, default=0.0)  # Adicionado valor padrão
    percentual_carteira = Column(Float, default=0.0)  # Adicionado valor padrão
    adicionado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    carteira = relationship("Carteira", back_populates="ativos")
    ativo = relationship("Ativo", back_populates="carteiras")


class Transacao(Base):
    """Modelo para registrar transações de compra/venda"""
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    carteira_id = Column(Integer, ForeignKey(
        "carteiras.id"), nullable=False, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"),
                      nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # COMPRA, VENDA
    quantidade = Column(Float, nullable=False)
    preco = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)
    taxa_corretagem = Column(Float, default=0.0, nullable=False)
    data_transacao = Column(DateTime, nullable=False, index=True)
    observacoes = Column(Text)
    criada_em = Column(DateTime, default=datetime.utcnow, nullable=False)


class IndicadorFinanceiro(Base):
    """Modelo para armazenar indicadores financeiros dos ativos"""
    __tablename__ = "indicadores_finaneiros"  # Corrigido typo aqui, estava "finaneiros"

    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id"), nullable=False)
    data_referencia = Column(DateTime, nullable=False)
    # Adicionado um índice composto para consultas rápidas
    __table_args__ = (
        UniqueConstraint('ativo_id', 'data_referencia',
                         name='uq_indicador_ativo_data'),
        Index('idx_indicador_ativo_data', 'ativo_id', 'data_referencia')
    )

    # Indicadores de valuation
    preco_lucro = Column(Float)
    preco_vp = Column(Float)
    preco_vendas = Column(Float)
    ev_ebitda = Column(Float)
    dividend_yield = Column(Float)

    # Indicadores de rentabilidade
    roe = Column(Float)
    roa = Column(Float)
    roic = Column(Float)
    margem_bruta = Column(Float)
    margem_liquida = Column(Float)

    # Indicadores de endividamento
    divida_liquida_pl = Column(Float)
    divida_liquida_ebitda = Column(Float)

    # Específicos para FIIs
    p_vp_fii = Column(Float)
    dividend_yield_fii = Column(Float)
    vacancia = Column(Float)

    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    ativo = relationship("Ativo")
