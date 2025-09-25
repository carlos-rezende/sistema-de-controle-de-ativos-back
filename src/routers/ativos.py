# src/routers/ativos.py (ou onde quer que seus routers estejam)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src import schemas
from src import crud

router = APIRouter(prefix="/ativos", tags=["Ativos"])

# Rota para listar todos os ativos


@router.get("/", response_model=List[schemas.Ativo], summary="Lista todos os ativos do sistema")
def get_all_ativos(db: Session = Depends(get_db)):
    """
    Retorna uma lista de todos os ativos financeiros cadastrados.
    """
    ativos = crud.get_ativos(db)
    return ativos

# Rota para criar um novo ativo


@router.post("/", response_model=schemas.Ativo, status_code=status.HTTP_201_CREATED, summary="Cria um novo ativo")
def create_ativo(ativo_create: schemas.AtivoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo ativo financeiro no sistema.
    """
    db_ativo = crud.get_ativo_by_ticker(db, ticker=ativo_create.ticker)
    if db_ativo:
        raise HTTPException(status_code=400, detail="Ticker já registrado")
    return crud.create_ativo(db, ativo=ativo_create)

# Opcional: Rota para buscar um ativo por ticker


@router.get("/{ticker}", response_model=schemas.Ativo, summary="Obtém um ativo por ticker")
def get_ativo(ticker: str, db: Session = Depends(get_db)):
    """
    Busca um ativo específico pelo seu ticker.
    """
    db_ativo = crud.get_ativo_by_ticker(db, ticker.upper())
    if db_ativo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ativo não encontrado")
    return db_ativo
