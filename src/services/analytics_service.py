import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import base64

from models import Ativo, Cotacao, Dividendo, CarteiraAtivo
import crud

class AnalyticsService:
    """Serviço para análise de dados financeiros"""
    
    def __init__(self):
        # Configurações de estilo para gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def calcular_retorno_simples(self, preco_inicial: float, preco_final: float) -> float:
        """Calcula o retorno simples entre dois preços"""
        if preco_inicial == 0:
            return 0.0
        return (preco_final - preco_inicial) / preco_inicial
    
    def calcular_retorno_composto(self, precos: List[float]) -> List[float]:
        """Calcula os retornos compostos de uma série de preços"""
        if len(precos) < 2:
            return []
        
        retornos = []
        for i in range(1, len(precos)):
            if precos[i-1] != 0:
                retorno = (precos[i] / precos[i-1]) - 1
                retornos.append(retorno)
            else:
                retornos.append(0.0)
        
        return retornos
    
    def calcular_volatilidade(self, retornos: List[float], anualizar: bool = True) -> float:
        """Calcula a volatilidade (desvio padrão dos retornos)"""
        if len(retornos) < 2:
            return 0.0
        
        volatilidade = np.std(retornos, ddof=1)
        
        if anualizar:
            # Assumindo dados diários, multiplica por sqrt(252) para anualizar
            volatilidade *= np.sqrt(252)
        
        return volatilidade
    
    def calcular_sharpe_ratio(self, retornos: List[float], taxa_livre_risco: float = 0.1) -> float:
        """Calcula o índice Sharpe"""
        if len(retornos) < 2:
            return 0.0
        
        retorno_medio = np.mean(retornos) * 252  # Anualizado
        volatilidade = self.calcular_volatilidade(retornos, anualizar=True)
        
        if volatilidade == 0:
            return 0.0
        
        return (retorno_medio - taxa_livre_risco) / volatilidade
    
    def calcular_drawdown(self, precos: List[float]) -> Tuple[List[float], float]:
        """Calcula o drawdown de uma série de preços"""
        if len(precos) < 2:
            return [], 0.0
        
        # Calcula o valor acumulado
        valores_acumulados = np.array(precos)
        
        # Calcula o pico histórico
        picos = np.maximum.accumulate(valores_acumulados)
        
        # Calcula o drawdown
        drawdowns = (valores_acumulados - picos) / picos
        
        # Máximo drawdown
        max_drawdown = np.min(drawdowns)
        
        return drawdowns.tolist(), max_drawdown
    
    def analisar_ativo(self, db: Session, ticker: str, periodo_dias: int = 252) -> Dict:
        """Análise completa de um ativo"""
        ativo = crud.get_ativo_by_ticker(db, ticker)
        if not ativo:
            return {"error": "Ativo não encontrado"}
        
        # Busca cotações do período
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        cotacoes = crud.get_cotacoes_periodo(db, ativo.id, data_inicio, datetime.now())
        
        if len(cotacoes) < 2:
            return {"error": "Dados insuficientes para análise"}
        
        # Organiza os dados
        df = pd.DataFrame([{
            'data': c.data_hora,
            'preco': c.preco_fechamento,
            'volume': c.volume or 0
        } for c in cotacoes])
        
        df = df.sort_values('data')
        precos = df['preco'].tolist()
        
        # Cálculos de performance
        retornos = self.calcular_retorno_composto(precos)
        retorno_total = self.calcular_retorno_simples(precos[0], precos[-1])
        retorno_anualizado = (1 + retorno_total) ** (252 / len(precos)) - 1
        volatilidade = self.calcular_volatilidade(retornos)
        sharpe = self.calcular_sharpe_ratio(retornos)
        drawdowns, max_drawdown = self.calcular_drawdown(precos)
        
        # Busca dividendos do período
        dividendos = crud.get_dividendos_periodo(db, ativo.id, data_inicio, datetime.now())
        dividend_yield = sum(d.valor for d in dividendos) / precos[-1] if precos[-1] > 0 else 0
        
        # Estatísticas básicas
        preco_atual = precos[-1]
        preco_minimo = min(precos)
        preco_maximo = max(precos)
        volume_medio = df['volume'].mean()
        
        return {
            "ticker": ticker,
            "nome": ativo.nome_curto,
            "periodo_analise": periodo_dias,
            "performance": {
                "preco_atual": preco_atual,
                "preco_minimo": preco_minimo,
                "preco_maximo": preco_maximo,
                "retorno_total": retorno_total,
                "retorno_anualizado": retorno_anualizado,
                "volatilidade": volatilidade,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_drawdown,
                "dividend_yield": dividend_yield
            },
            "estatisticas": {
                "numero_observacoes": len(precos),
                "volume_medio": volume_medio,
                "numero_dividendos": len(dividendos)
            }
        }
    
    def comparar_ativos(self, db: Session, tickers: List[str], periodo_dias: int = 252) -> Dict:
        """Compara múltiplos ativos"""
        resultados = {}
        
        for ticker in tickers:
            analise = self.analisar_ativo(db, ticker, periodo_dias)
            if "error" not in analise:
                resultados[ticker] = analise
        
        if not resultados:
            return {"error": "Nenhum ativo válido para comparação"}
        
        # Cria tabela comparativa
        comparacao = []
        for ticker, dados in resultados.items():
            perf = dados["performance"]
            comparacao.append({
                "ticker": ticker,
                "nome": dados["nome"],
                "retorno_total": perf["retorno_total"],
                "retorno_anualizado": perf["retorno_anualizado"],
                "volatilidade": perf["volatilidade"],
                "sharpe_ratio": perf["sharpe_ratio"],
                "max_drawdown": perf["max_drawdown"],
                "dividend_yield": perf["dividend_yield"]
            })
        
        # Ordena por Sharpe ratio
        comparacao.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        
        return {
            "comparacao": comparacao,
            "detalhes": resultados
        }
    
    def analisar_carteira(self, db: Session, carteira_id: int) -> Dict:
        """Análise de uma carteira de investimentos"""
        carteira_ativos = crud.get_carteira_ativos(db, carteira_id)
        
        if not carteira_ativos:
            return {"error": "Carteira vazia ou não encontrada"}
        
        # Atualiza valores da carteira
        crud.atualizar_valor_carteira(db, carteira_id)
        crud.calcular_percentual_carteira(db, carteira_id)
        
        # Recarrega os dados atualizados
        carteira_ativos = crud.get_carteira_ativos(db, carteira_id)
        
        # Análise por ativo
        analise_ativos = []
        valor_total_carteira = 0
        
        for ca in carteira_ativos:
            ativo = ca.ativo
            valor_atual = ca.valor_atual or 0
            valor_investido = ca.valor_investido
            rentabilidade = valor_atual - valor_investido
            rentabilidade_pct = (rentabilidade / valor_investido * 100) if valor_investido > 0 else 0
            
            analise_ativos.append({
                "ticker": ativo.ticker,
                "nome": ativo.nome_curto,
                "quantidade": ca.quantidade,
                "preco_medio": ca.preco_medio,
                "valor_investido": valor_investido,
                "valor_atual": valor_atual,
                "rentabilidade": rentabilidade,
                "rentabilidade_percentual": rentabilidade_pct,
                "percentual_carteira": ca.percentual_carteira or 0
            })
            
            valor_total_carteira += valor_atual
        
        # Métricas da carteira
        total_investido = sum(a["valor_investido"] for a in analise_ativos)
        rentabilidade_total = valor_total_carteira - total_investido
        rentabilidade_total_pct = (rentabilidade_total / total_investido * 100) if total_investido > 0 else 0
        
        # Diversificação
        concentracao_maxima = max(a["percentual_carteira"] for a in analise_ativos) if analise_ativos else 0
        numero_ativos = len(analise_ativos)
        
        # Análise por setor (se disponível)
        setores = {}
        for ca in carteira_ativos:
            setor = ca.ativo.setor or "Não classificado"
            if setor not in setores:
                setores[setor] = {"valor": 0, "percentual": 0}
            setores[setor]["valor"] += ca.valor_atual or 0
        
        for setor in setores:
            setores[setor]["percentual"] = (setores[setor]["valor"] / valor_total_carteira * 100) if valor_total_carteira > 0 else 0
        
        return {
            "carteira_id": carteira_id,
            "resumo": {
                "valor_total": valor_total_carteira,
                "total_investido": total_investido,
                "rentabilidade_total": rentabilidade_total,
                "rentabilidade_percentual": rentabilidade_total_pct,
                "numero_ativos": numero_ativos,
                "concentracao_maxima": concentracao_maxima
            },
            "ativos": analise_ativos,
            "diversificacao_setorial": setores
        }
    
    def gerar_grafico_performance(self, db: Session, ticker: str, periodo_dias: int = 252) -> str:
        """Gera gráfico de performance de um ativo"""
        ativo = crud.get_ativo_by_ticker(db, ticker)
        if not ativo:
            return ""
        
        # Busca dados
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        cotacoes = crud.get_cotacoes_periodo(db, ativo.id, data_inicio, datetime.now())
        
        if len(cotacoes) < 2:
            return ""
        
        # Prepara dados
        df = pd.DataFrame([{
            'data': c.data_hora,
            'preco': c.preco_fechamento,
            'volume': c.volume or 0
        } for c in cotacoes])
        
        df = df.sort_values('data')
        
        # Cria gráfico com Plotly
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'Preço - {ticker}', 'Volume'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Gráfico de preço
        fig.add_trace(
            go.Scatter(
                x=df['data'],
                y=df['preco'],
                mode='lines',
                name='Preço',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # Gráfico de volume
        fig.add_trace(
            go.Bar(
                x=df['data'],
                y=df['volume'],
                name='Volume',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # Layout
        fig.update_layout(
            title=f'Análise de Performance - {ativo.nome_curto}',
            xaxis_title='Data',
            height=600,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="Preço (R$)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        # Converte para HTML
        return fig.to_html(include_plotlyjs='cdn')
    
    def gerar_relatorio_carteira(self, db: Session, carteira_id: int) -> Dict:
        """Gera relatório completo da carteira"""
        analise = self.analisar_carteira(db, carteira_id)
        
        if "error" in analise:
            return analise
        
        # Gera gráfico de distribuição
        ativos_data = analise["ativos"]
        
        # Gráfico de pizza - Distribuição por ativo
        fig_pizza = go.Figure(data=[go.Pie(
            labels=[a["ticker"] for a in ativos_data],
            values=[a["percentual_carteira"] for a in ativos_data],
            hole=0.3
        )])
        
        fig_pizza.update_layout(
            title="Distribuição da Carteira por Ativo",
            annotations=[dict(text='Carteira', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        # Gráfico de barras - Rentabilidade por ativo
        fig_barras = go.Figure(data=[
            go.Bar(
                x=[a["ticker"] for a in ativos_data],
                y=[a["rentabilidade_percentual"] for a in ativos_data],
                marker_color=['green' if x >= 0 else 'red' for x in [a["rentabilidade_percentual"] for a in ativos_data]]
            )
        ])
        
        fig_barras.update_layout(
            title="Rentabilidade por Ativo (%)",
            xaxis_title="Ativo",
            yaxis_title="Rentabilidade (%)"
        )
        
        # Gráfico de setores se houver dados
        setores_data = analise["diversificacao_setorial"]
        fig_setores = None
        
        if len(setores_data) > 1:
            fig_setores = go.Figure(data=[go.Pie(
                labels=list(setores_data.keys()),
                values=[s["percentual"] for s in setores_data.values()]
            )])
            
            fig_setores.update_layout(title="Diversificação por Setor")
        
        return {
            "analise": analise,
            "graficos": {
                "distribuicao_ativos": fig_pizza.to_html(include_plotlyjs='cdn'),
                "rentabilidade_ativos": fig_barras.to_html(include_plotlyjs='cdn'),
                "distribuicao_setores": fig_setores.to_html(include_plotlyjs='cdn') if fig_setores else None
            }
        }

# Instância global do serviço
analytics_service = AnalyticsService()

