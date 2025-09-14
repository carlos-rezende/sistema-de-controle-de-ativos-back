import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BrapiService:
    """Serviço para integração com a API brapi.dev"""
    
    def __init__(self):
        self.base_url = os.getenv("BRAPI_BASE_URL", "https://brapi.dev/api")
        self.token = os.getenv("BRAPI_TOKEN", "")
        self.headers = {}
        
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Faz uma requisição para a API brapi.dev"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url}: {e}")
            return {"error": str(e)}
    
    def get_quote(self, tickers: List[str], **kwargs) -> Dict:
        """
        Busca cotações de ativos
        
        Args:
            tickers: Lista de tickers para buscar
            **kwargs: Parâmetros adicionais (range, interval, fundamental, dividends, modules)
        
        Returns:
            Dados das cotações
        """
        tickers_str = ",".join(tickers)
        endpoint = f"quote/{tickers_str}"
        
        params = {}
        if self.token:
            params["token"] = self.token
            
        # Adiciona parâmetros opcionais
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
        
        return self._make_request(endpoint, params)
    
    def get_quote_list(self, **kwargs) -> Dict:
        """
        Busca lista de todas as ações disponíveis
        
        Args:
            **kwargs: Parâmetros adicionais
        
        Returns:
            Lista de ações
        """
        endpoint = "quote/list"
        
        params = {}
        if self.token:
            params["token"] = self.token
            
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
        
        return self._make_request(endpoint, params)
    
    def get_historical_data(self, ticker: str, range_period: str = "1mo", 
                          interval: str = "1d") -> Dict:
        """
        Busca dados históricos de um ativo
        
        Args:
            ticker: Ticker do ativo
            range_period: Período dos dados (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalo dos dados (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            Dados históricos
        """
        params = {
            "range": range_period,
            "interval": interval
        }
        
        if self.token:
            params["token"] = self.token
        
        return self.get_quote([ticker], **params)
    
    def get_dividends(self, ticker: str) -> Dict:
        """
        Busca dados de dividendos de um ativo
        
        Args:
            ticker: Ticker do ativo
        
        Returns:
            Dados de dividendos
        """
        params = {"dividends": "true"}
        
        if self.token:
            params["token"] = self.token
        
        return self.get_quote([ticker], **params)
    
    def get_fundamental_data(self, ticker: str, modules: List[str] = None) -> Dict:
        """
        Busca dados fundamentalistas de um ativo
        
        Args:
            ticker: Ticker do ativo
            modules: Lista de módulos a serem incluídos
        
        Returns:
            Dados fundamentalistas
        """
        params = {"fundamental": "true"}
        
        if modules:
            params["modules"] = ",".join(modules)
        
        if self.token:
            params["token"] = self.token
        
        return self.get_quote([ticker], **params)
    
    def get_crypto_quote(self, coins: List[str]) -> Dict:
        """
        Busca cotações de criptomoedas
        
        Args:
            coins: Lista de símbolos de criptomoedas
        
        Returns:
            Cotações de criptomoedas
        """
        coins_str = ",".join(coins)
        endpoint = f"crypto/{coins_str}"
        
        params = {}
        if self.token:
            params["token"] = self.token
        
        return self._make_request(endpoint, params)
    
    def get_currency_quote(self, currencies: List[str]) -> Dict:
        """
        Busca cotações de moedas
        
        Args:
            currencies: Lista de códigos de moedas
        
        Returns:
            Cotações de moedas
        """
        currencies_str = ",".join(currencies)
        endpoint = f"currency/{currencies_str}"
        
        params = {}
        if self.token:
            params["token"] = self.token
        
        return self._make_request(endpoint, params)
    
    def get_inflation(self, country: str = "BR") -> Dict:
        """
        Busca dados de inflação
        
        Args:
            country: Código do país (padrão: BR)
        
        Returns:
            Dados de inflação
        """
        endpoint = f"inflation/{country}"
        
        params = {}
        if self.token:
            params["token"] = self.token
        
        return self._make_request(endpoint, params)
    
    def get_selic_rate(self) -> Dict:
        """
        Busca taxa SELIC
        
        Returns:
            Dados da taxa SELIC
        """
        endpoint = "selic"
        
        params = {}
        if self.token:
            params["token"] = self.token
        
        return self._make_request(endpoint, params)
    
    def parse_quote_data(self, data: Dict) -> List[Dict]:
        """
        Processa dados de cotação da API brapi.dev
        
        Args:
            data: Dados retornados pela API
        
        Returns:
            Lista de dados processados
        """
        if "results" not in data:
            return []
        
        processed_data = []
        
        for result in data["results"]:
            processed_item = {
                "ticker": result.get("symbol", ""),
                "nome_curto": result.get("shortName", ""),
                "nome_longo": result.get("longName", ""),
                "moeda": result.get("currency", "BRL"),
                "preco_fechamento": result.get("regularMarketPrice", 0.0),
                "preco_abertura": result.get("regularMarketPreviousClose", 0.0),
                "preco_maximo": result.get("regularMarketDayHigh", 0.0),
                "preco_minimo": result.get("regularMarketDayLow", 0.0),
                "volume": result.get("regularMarketVolume", 0),
                "variacao": result.get("regularMarketChange", 0.0),
                "variacao_percentual": result.get("regularMarketChangePercent", 0.0),
                "valor_mercado": result.get("marketCap", 0.0),
                "logo_url": result.get("logourl", ""),
                "data_hora": datetime.now()
            }
            
            # Processa dados históricos se disponíveis
            if "historicalDataPrice" in result:
                historical_data = []
                for hist in result["historicalDataPrice"]:
                    historical_data.append({
                        "data": datetime.fromtimestamp(hist.get("date", 0)),
                        "abertura": hist.get("open", 0.0),
                        "maximo": hist.get("high", 0.0),
                        "minimo": hist.get("low", 0.0),
                        "fechamento": hist.get("close", 0.0),
                        "volume": hist.get("volume", 0)
                    })
                processed_item["historico"] = historical_data
            
            # Processa dados de dividendos se disponíveis
            if "dividendsData" in result:
                dividends_data = []
                for div in result["dividendsData"]["cashDividends"]:
                    dividends_data.append({
                        "tipo": "DIVIDENDO",
                        "valor": div.get("rate", 0.0),
                        "data_com": datetime.strptime(div.get("date", ""), "%Y-%m-%d") if div.get("date") else None,
                        "data_ex": datetime.strptime(div.get("exDate", ""), "%Y-%m-%d") if div.get("exDate") else None,
                        "data_pagamento": datetime.strptime(div.get("paymentDate", ""), "%Y-%m-%d") if div.get("paymentDate") else None
                    })
                processed_item["dividendos"] = dividends_data
            
            processed_data.append(processed_item)
        
        return processed_data

# Instância global do serviço
brapi_service = BrapiService()

