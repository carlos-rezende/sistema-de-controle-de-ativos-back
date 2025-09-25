from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# --- Enums para padronizar valores ---


class TipoAtivo(str, Enum):
    ACAO = "ACAO"
    FII = "FII"
    ETF = "ETF"
    BDR = "BDR"
    INDICE = "INDICE"
    CRIPTO = "CRIPTO"  # Adicionando CRIPTO
    MOEDA = "MOEDA"   # Adicionando MOEDA


class TipoTransacao(str, Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"


class TipoDividendo(str, Enum):
    DIVIDENDO = "DIVIDENDO"
    JCP = "JCP"
    BONIFICACAO = "BONIFICACAO"

# --- Schemas para Cotação ---


class CotacaoBase(BaseModel):
    data_hora: datetime
    preco_abertura: Optional[float] = None
    preco_maximo: Optional[float] = None
    preco_minimo: Optional[float] = None
    preco_fechamento: float
    volume: Optional[int] = None
    variacao: Optional[float] = None
    variacao_percentual: Optional[float] = None
    valor_mercado: Optional[float] = None


class CotacaoCreate(CotacaoBase):
    ativo_id: int


class Cotacao(CotacaoBase):
    id: int
    ativo_id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# --- Schemas para Dividendo ---


class DividendoBase(BaseModel):
    tipo: TipoDividendo
    valor: float
    data_com: Optional[datetime] = None
    data_ex: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None


class DividendoCreate(DividendoBase):
    ativo_id: int


class Dividendo(DividendoBase):
    id: int
    ativo_id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# --- Schemas para Ativo ---


class AtivoBase(BaseModel):
    ticker: str = Field(..., max_length=10)
    nome_curto: str = Field(..., max_length=100)
    nome_longo: Optional[str] = Field(None, max_length=200)
    tipo: TipoAtivo
    setor: Optional[str] = Field(None, max_length=100)
    subsetor: Optional[str] = Field(None, max_length=100)
    moeda: str = Field(default="BRL", max_length=3)
    logo_url: Optional[str] = Field(None, max_length=500)
    ativo: bool = Field(default=True)


class AtivoCreate(AtivoBase):
    pass


class AtivoUpdate(BaseModel):
    nome_curto: Optional[str] = Field(None, max_length=100)
    nome_longo: Optional[str] = Field(None, max_length=200)
    setor: Optional[str] = Field(None, max_length=100)
    subsetor: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)
    ativo: Optional[bool] = None


class Ativo(AtivoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    cotacoes: List[Cotacao] = []
    dividendos: List[Dividendo] = []

    class Config:
        from_attributes = True

# --- Schemas para CarteiraAtivo ---


class CarteiraAtivoBase(BaseModel):
    quantidade: float
    preco_medio: float
    valor_investido: float


class CarteiraAtivoCreate(CarteiraAtivoBase):
    carteira_id: int
    ativo_id: int


class CarteiraAtivoUpdate(BaseModel):
    quantidade: Optional[float] = None
    preco_medio: Optional[float] = None


class CarteiraAtivo(CarteiraAtivoBase):
    id: int
    carteira_id: int
    ativo_id: int
    valor_atual: Optional[float] = None
    percentual_carteira: Optional[float] = None
    adicionado_em: datetime
    atualizado_em: datetime

    ativo: "Ativo"

    class Config:
        from_attributes = True

# --- Schemas para Carteira ---


class CarteiraBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = None
    ativa: bool = Field(default=True)


class CarteiraCreate(CarteiraBase):
    pass


class CarteiraUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


class Carteira(CarteiraBase):
    id: int
    valor_total: float = Field(default=0.0)
    criada_em: datetime
    atualizada_em: datetime

    ativos: List[CarteiraAtivo] = []

    class Config:
        from_attributes = True

# --- Schemas para Transação ---


class TransacaoBase(BaseModel):
    tipo: TipoTransacao
    quantidade: float
    preco: float
    valor_total: float
    taxa_corretagem: float = Field(default=0.0)
    data_transacao: datetime
    observacoes: Optional[str] = None


class TransacaoCreate(TransacaoBase):
    carteira_id: int
    ativo_id: int


class Transacao(TransacaoBase):
    id: int
    carteira_id: int
    ativo_id: int
    criada_em: datetime

    class Config:
        from_attributes = True

# --- Schemas para Indicadores Financeiros ---


class IndicadorFinanceiroBase(BaseModel):
    data_referencia: datetime
    preco_lucro: Optional[float] = None
    preco_vp: Optional[float] = None
    preco_vendas: Optional[float] = None
    ev_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    margem_bruta: Optional[float] = None
    margem_liquida: Optional[float] = None
    divida_liquida_pl: Optional[float] = None
    divida_liquida_ebitda: Optional[float] = None
    p_vp_fii: Optional[float] = None
    dividend_yield_fii: Optional[float] = None
    vacancia: Optional[float] = None


class IndicadorFinanceiroCreate(IndicadorFinanceiroBase):
    ativo_id: int


class IndicadorFinanceiro(IndicadorFinanceiroBase):
    id: int
    ativo_id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------------------
# --- NOVOS SCHEMAS PARA AS ROTAS DE ANÁLISE (ADICIONADOS AQUI) ---
# -------------------------------------------------------------

# Schema para o endpoint de análise de um único ativo


class AnalisePerformance(BaseModel):
    preco_atual: float
    preco_minimo: float
    preco_maximo: float
    retorno_total: float
    retorno_anualizado: float
    volatilidade: float
    sharpe_ratio: float
    max_drawdown: float
    dividend_yield: Optional[float] = None


class AnaliseEstatisticas(BaseModel):
    numero_observacoes: int
    volume_medio: float
    numero_dividendos: Optional[int] = None


class AnaliseAtivoResponse(BaseModel):
    ticker: str
    nome: str
    periodo_analise: int
    performance: AnalisePerformance
    estatisticas: AnaliseEstatisticas

# Schemas para o endpoint de comparação de ativos


class CompararAtivosRequest(BaseModel):
    tickers: List[str]
    periodo_dias: int = 252


class ComparacaoDetalhes(BaseModel):
    ticker: str
    nome: str
    retorno_total: float
    retorno_anualizado: float
    volatilidade: float
    sharpe_ratio: float
    max_drawdown: float
    dividend_yield: float


class ComparacaoAtivosResponse(BaseModel):
    comparacao: List[ComparacaoDetalhes]
    detalhes: Dict[str, AnaliseAtivoResponse]

# Schema para a análise de carteira


class AnaliseCarteiraResponse(BaseModel):
    carteira_id: int
    resumo: Dict
    ativos: List[Dict]
    diversificacao_setorial: Dict

# Schema para as métricas do mercado


class MetricasMercadoResponse(BaseModel):
    total_ativos: int
    distribuicao_tipos: Dict
    distribuicao_setores: Dict
    ativos_recentes: List[Dict]

# --- Schemas para Respostas da API (gerais) ---


class ResponseMessage(BaseModel):
    message: str
    success: bool = True


class AtivoComCotacao(AtivoBase):
    id: int
    ultima_cotacao: Optional[Cotacao] = None
    dividendos_recentes: List[Dividendo] = []

    class Config:
        from_attributes = True

# Schemas para busca de dados externos


class BuscaAtivoRequest(BaseModel):
    tickers: List[str] = Field(..., description="Lista de tickers para buscar")
    incluir_historico: bool = Field(
        default=False, description="Incluir dados históricos")
    incluir_dividendos: bool = Field(
        default=False, description="Incluir dados de dividendos")
    range_historico: Optional[str] = Field(
        default="1mo", description="Período para dados históricos")


class AtualizacaoPrecos(BaseModel):
    tickers_atualizados: List[str]
    total_cotacoes: int
    sucesso: bool
    mensagem: str


# Importação da frente para a declaração, para resolver problemas de importação circular
# no Pydantic quando há modelos que referenciam uns aos outros
CarteiraAtivo.model_rebuild()
