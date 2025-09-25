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

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Faz uma requisição para a API brapi.dev de forma centralizada.
        Agora, a lógica do token é tratada aqui, evitando repetição.
        """
        url = f"{self.base_url}/{endpoint}"

        if params is None:
            params = {}

        if self.token:
            params["token"] = self.token

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP na requisição para {url}: {e}")
            print(
                f"URL: {response.url}, Status: {response.status_code}, Resposta: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url}: {e}")
            return None

    def get_quote(self, tickers: List[str], **kwargs) -> Optional[Dict]:
        """
        Busca cotações de ativos.
        """
        tickers_str = ",".join(tickers)
        endpoint = f"quote/{tickers_str}"
        return self._make_request(endpoint, params=kwargs)

    def get_quote_list(self, **kwargs) -> Optional[Dict]:
        """
        Busca lista de todas as ações disponíveis.
        """
        endpoint = "quote/list"
        return self._make_request(endpoint, params=kwargs)

    # ✅ CORREÇÃO: O método get_historical_data agora chama get_quote
    def get_historical_data(self, ticker: str, range_period: str = "1mo", interval: str = "1d") -> Optional[Dict]:
        """
        Busca dados históricos de um ativo usando get_quote.
        """
        return self.get_quote([ticker], range=range_period, interval=interval)

    def get_dividends(self, ticker: str) -> Optional[Dict]:
        """
        Busca dados de dividendos de um ativo.
        """
        params = {"dividends": "true"}
        return self.get_quote([ticker], **params)

    def get_fundamental_data(self, ticker: str, modules: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Busca dados fundamentalistas de um ativo.
        """
        params = {"fundamental": "true"}
        if modules:
            params["modules"] = ",".join(modules)
        return self.get_quote([ticker], **params)

    def get_crypto_quote(self, coins: List[str]) -> Optional[Dict]:
        """
        Busca cotações de criptomoedas.
        """
        coins_str = ",".join(coins)
        endpoint = f"crypto/{coins_str}"
        return self._make_request(endpoint)

    def get_currency_quote(self, currencies: List[str]) -> Optional[Dict]:
        """
        Busca cotações de moedas.
        """
        currencies_str = ",".join(currencies)
        endpoint = f"currency/{currencies_str}"
        return self._make_request(endpoint)

    def get_inflation(self, country: str = "BR") -> Optional[Dict]:
        """
        Busca dados de inflação.
        """
        endpoint = f"inflation/{country}"
        return self._make_request(endpoint)

    def get_selic_rate(self) -> Optional[Dict]:
        """
        Busca taxa SELIC.
        """
        endpoint = "selic"
        return self._make_request(endpoint)

    def parse_quote_data(self, data: Optional[Dict]) -> List[Dict]:
        """
        Processa dados de cotação da API brapi.dev.
        """
        if not data or "results" not in data:
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

            historical_data = result.get("historicalDataPrice")
            if historical_data:
                processed_item["historico"] = [
                    {
                        "data": datetime.fromtimestamp(hist.get("date", 0)),
                        "abertura": hist.get("open", 0.0),
                        "maximo": hist.get("high", 0.0),
                        "minimo": hist.get("low", 0.0),
                        "fechamento": hist.get("close", 0.0),
                        "volume": hist.get("volume", 0)
                    } for hist in historical_data
                ]

            dividends_data = result.get(
                "dividendsData", {}).get("cashDividends")
            if dividends_data:
                processed_item["dividendos"] = [
                    {
                        "tipo": "DIVIDENDO",
                        "valor": div.get("rate", 0.0),
                        "data_com": datetime.strptime(div["date"], "%Y-%m-%d") if "date" in div else None,
                        "data_ex": datetime.strptime(div["exDate"], "%Y-%m-%d") if "exDate" in div else None,
                        "data_pagamento": datetime.strptime(div["paymentDate"], "%Y-%m-%d") if "paymentDate" in div else None
                    } for div in dividends_data
                ]

            processed_data.append(processed_item)

        return processed_data


# Instância global do serviço
brapi_service = BrapiService()
