import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.models import Ativo, CarteiraAtivo
from src import crud
from src.services.brapi_service import BrapiService


class AnalyticsService:
    """Serviço para análise de dados financeiros"""

    def __init__(self, db: Session):
        self.db = db
        # BrapiService deve aceitar token no __init__
        self.brapi_service = BrapiService()
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    # ===========================
    # ===== MÉTRICAS BÁSICAS ====
    # ===========================
    def calcular_retorno_simples(self, preco_inicial: float, preco_final: float) -> float:
        if preco_inicial == 0:
            return 0.0
        return (preco_final - preco_inicial) / preco_inicial

    def calcular_retorno_composto(self, precos: List[float]) -> List[float]:
        if len(precos) < 2:
            return []
        return (np.array(precos[1:]) / np.array(precos[:-1]) - 1).tolist()

    def calcular_volatilidade(self, retornos: List[float], anualizar: bool = True) -> float:
        if len(retornos) < 2:
            return 0.0
        vol = np.std(retornos, ddof=1)
        return vol * np.sqrt(252) if anualizar else vol

    def calcular_sharpe_ratio(self, retornos: List[float], taxa_livre_risco: float = 0.05) -> float:
        if len(retornos) < 2:
            return 0.0
        media = np.mean(retornos) * 252
        vol = self.calcular_volatilidade(retornos, anualizar=True)
        return (media - taxa_livre_risco) / vol if vol > 0 else 0.0

    def calcular_drawdown(self, precos: List[float]) -> Tuple[List[float], float]:
        if len(precos) < 2:
            return [], 0.0
        serie = pd.Series(precos)
        pico = serie.cummax()
        dd = (serie - pico) / pico
        return dd.tolist(), dd.min()

    # ===========================
    # ===== BUSCA DE DADOS ======
    # ===========================
    def _get_dataframe(self, ticker: str, periodo_dias: int) -> Optional[pd.DataFrame]:
        """
        Busca cotações na BRAPI e cria um DataFrame,
        respeitando os limites do plano gratuito (1d, 5d, 1mo, 3mo).
        """
        # Escolha do range permitido
        if periodo_dias >= 252:       # ~1 ano
            print("⚠️ Plano gratuito não suporta 1y. Usando 3mo.")
            range_param = '3mo'
        elif periodo_dias >= 90:
            range_param = '3mo'
        elif periodo_dias >= 30:
            range_param = '1mo'
        elif periodo_dias >= 5:
            range_param = '5d'
        else:
            range_param = '1d'

        try:
            # 🔑 Somente parâmetros permitidos no plano gratuito
            cotacoes_data = self.brapi_service.get_historical_data(
                ticker,
                range_period=range_param,
                interval='1d'
            )
        except Exception as e:
            print(f"⚠️ Erro na requisição BRAPI: {e}")
            return None

        # A resposta vem em results[0]['historicalDataPrice']
        if not cotacoes_data or "results" not in cotacoes_data:
            print("⚠️ Dados inválidos ou limite da API atingido.")
            return None

        results = cotacoes_data["results"]
        if not results or "historicalDataPrice" not in results[0]:
            print("⚠️ Histórico não disponível para este ticker.")
            return None

        df = pd.DataFrame(results[0]["historicalDataPrice"])
        if df.empty:
            return None

        df['data'] = pd.to_datetime(df['date'], unit='s', errors='coerce')
        df = df.rename(
            columns={'close': 'preco_fechamento', 'volume': 'volume'})
        df = df.dropna(subset=['data', 'preco_fechamento'])
        return df.sort_values('data').set_index('data')

    # ===========================
    # ===== ANÁLISE DE ATIVO ====
    # ===========================
    def analisar_ativo(self, ticker: str, periodo_dias: int = 252) -> Dict:
        ativo = crud.get_ativo_by_ticker(self.db, ticker)
        if not ativo:
            return {"error": "Ativo não encontrado"}

        df = self._get_dataframe(ticker, periodo_dias)
        if df is None:
            return {"error": "Dados insuficientes para análise ou limite do plano atingido."}

        precos = df['preco_fechamento'].tolist()
        retornos = self.calcular_retorno_composto(precos)
        retorno_total = self.calcular_retorno_simples(precos[0], precos[-1])
        retorno_anual = (1 + retorno_total) ** (252 / len(precos)) - 1
        volatilidade = self.calcular_volatilidade(retornos)
        sharpe = self.calcular_sharpe_ratio(retornos)
        drawdowns, max_drawdown = self.calcular_drawdown(precos)

        return {
            "ticker": ticker,
            "nome": ativo.nome_curto,
            "periodo_analise": periodo_dias,
            "performance": {
                "preco_atual": precos[-1],
                "preco_minimo": df['preco_fechamento'].min(),
                "preco_maximo": df['preco_fechamento'].max(),
                "retorno_total": retorno_total,
                "retorno_anualizado": retorno_anual,
                "volatilidade": volatilidade,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_drawdown
            },
            "estatisticas": {
                "numero_observacoes": len(precos),
                "volume_medio": df['volume'].mean()
            }
        }

    # ===========================
    # ===== COMPARAR ATIVOS =====
    # ===========================
    def comparar_ativos(self, tickers: List[str], periodo_dias: int = 252) -> Dict:
        resultados = {t: self.analisar_ativo(t, periodo_dias) for t in tickers}
        validos = {k: v for k, v in resultados.items() if "error" not in v}
        if not validos:
            return {"error": "Nenhum ativo válido para comparação."}

        comparacao = [
            {"ticker": t, "nome": d["nome"], **d["performance"]}
            for t, d in validos.items()
        ]
        comparacao.sort(key=lambda x: x.get("sharpe_ratio", -1), reverse=True)
        return {"comparacao": comparacao, "detalhes": validos}

    # ===========================
    # ===== ANÁLISE CARTEIRA ====
    # ===========================
    def analisar_carteira(self, carteira_id: int) -> Dict:
        carteira_ativos = crud.get_carteira_ativos(self.db, carteira_id)
        if not carteira_ativos:
            return {"error": "Carteira vazia ou não encontrada"}

        ativos_data, total_atual, total_invest = [], 0, 0
        for ca in carteira_ativos:
            investido = ca.valor_investido
            atual = ca.valor_atual or 0
            rentab = atual - investido
            pct = rentab / investido * 100 if investido > 0 else 0
            ativos_data.append({
                "ticker": ca.ativo.ticker,
                "nome": ca.ativo.nome_curto,
                "quantidade": ca.quantidade,
                "preco_medio": ca.preco_medio,
                "valor_investido": investido,
                "valor_atual": atual,
                "rentabilidade": rentab,
                "rentabilidade_percentual": pct,
                "percentual_carteira": ca.percentual_carteira or 0
            })
            total_atual += atual
            total_invest += investido

        rentab_total = total_atual - total_invest
        rentab_pct = rentab_total / total_invest * 100 if total_invest > 0 else 0

        setores: Dict[str, Dict[str, float]] = {}
        for ca in carteira_ativos:
            setor = ca.ativo.setor or "Não classificado"
            setores.setdefault(setor, {"valor": 0})
            setores[setor]["valor"] += ca.valor_atual or 0
        for s in setores:
            setores[s]["percentual"] = (
                setores[s]["valor"] / total_atual * 100
            ) if total_atual > 0 else 0

        return {
            "carteira_id": carteira_id,
            "resumo": {
                "valor_total": total_atual,
                "total_investido": total_invest,
                "rentabilidade_total": rentab_total,
                "rentabilidade_percentual": rentab_pct,
                "numero_ativos": len(ativos_data),
                "concentracao_maxima": max((a["percentual_carteira"] for a in ativos_data), default=0)
            },
            "ativos": ativos_data,
            "diversificacao_setorial": setores
        }

    # ===========================
    # ===== GRÁFICOS ============
    # ===========================
    def gerar_grafico_performance(self, ticker: str, periodo_dias: int = 252) -> Optional[str]:
        ativo = crud.get_ativo_by_ticker(self.db, ticker)
        if not ativo:
            return None
        df = self._get_dataframe(ticker, periodo_dias)
        if df is None:
            return None

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'Preço - {ticker}', 'Volume'),
            vertical_spacing=0.1, row_heights=[0.7, 0.3]
        )
        fig.add_trace(go.Scatter(
            x=df.index, y=df['preco_fechamento'], mode='lines',
            name='Preço', line=dict(color='blue', width=2)
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=df.index, y=df['volume'], name='Volume',
            marker_color='lightblue'
        ), row=2, col=1)
        fig.update_layout(
            title_text=f'Análise de Performance - {ativo.nome_curto}',
            xaxis_rangeslider_visible=False,
            xaxis2_rangeslider_visible=False,
            height=600, showlegend=True
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def gerar_relatorio_carteira(self, carteira_id: int) -> Dict:
        analise = self.analisar_carteira(carteira_id)
        if "error" in analise:
            return analise

        ativos_data = analise["ativos"]
        setores_data = analise["diversificacao_setorial"]
        graficos = {}

        if ativos_data:
            fig_pizza = px.pie(
                values=[a["percentual_carteira"] for a in ativos_data],
                names=[a["ticker"] for a in ativos_data],
                title="Distribuição da Carteira por Ativo", hole=0.3
            )
            graficos["distribuicao_ativos"] = fig_pizza.to_html(
                full_html=False, include_plotlyjs='cdn')

            fig_barras = px.bar(
                x=[a["ticker"] for a in ativos_data],
                y=[a["rentabilidade_percentual"] for a in ativos_data],
                color=[a["rentabilidade_percentual"]
                       >= 0 for a in ativos_data],
                color_discrete_map={True: 'green', False: 'red'},
                title="Rentabilidade por Ativo (%)",
                labels={'x': 'Ativo', 'y': 'Rentabilidade (%)'}
            )
            fig_barras.update_layout(showlegend=False)
            graficos["rentabilidade_ativos"] = fig_barras.to_html(
                full_html=False, include_plotlyjs='cdn')

        if len(setores_data) > 1:
            fig_setores = px.pie(
                values=[s["percentual"] for s in setores_data.values()],
                names=list(setores_data.keys()),
                title="Diversificação por Setor"
            )
            graficos["distribuicao_setores"] = fig_setores.to_html(
                full_html=False, include_plotlyjs='cdn')

        return {"analise": analise, "graficos": graficos}

    # ===========================
    # ===== MÉTRICAS GERAIS =====
    # ===========================
    def analisar_metricas_mercado(self) -> Dict:
        ativos = crud.get_ativos(self.db, limit=1000)
        tipos, setores = {}, {}

        for a in ativos:
            tipos[a.tipo] = tipos.get(a.tipo, 0) + 1
            setor = a.setor or "Não classificado"
            setores[setor] = setores.get(setor, 0) + 1

        return {
            "total_ativos": len(ativos),
            "distribuicao_tipos": tipos,
            "distribuicao_setores": setores,
            "ativos_recentes": [
                {"ticker": a.ticker, "nome": a.nome_curto,
                 "tipo": a.tipo, "setor": a.setor}
                for a in ativos[:10]
            ]
        }
