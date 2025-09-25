from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# --- Importações Corrigidas ---
# Use a importação absoluta para garantir que o FastAPI encontre os módulos corretos.
from src.database import get_db
from src import crud
from src import schemas

router = APIRouter(prefix="/wallet", tags=["Wallet & Transactions"])

# O restante do seu código está excelente e não precisa de alterações.
# Abaixo, segue o código completo para sua conveniência.

# --- Rotas para Carteiras ---


@router.post(
    "/",
    response_model=schemas.Carteira,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova carteira"
)
def create_wallet(
    carteira_create: schemas.CarteiraCreate,
    db: Session = Depends(get_db)
):
    """
    Cria uma nova carteira de investimento com um nome e descrição.
    """
    return crud.create_carteira(db, carteira=carteira_create)


@router.get(
    "/{carteira_id}",
    response_model=schemas.Carteira,
    summary="Obtém uma carteira por ID"
)
def get_wallet(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Busca e retorna uma carteira de investimento específica.
    """
    db_carteira = crud.get_carteira(db, carteira_id=carteira_id)
    if db_carteira is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")

    # Atualiza valor e percentual antes de retornar para garantir dados corretos
    crud.atualizar_valor_carteira(db, carteira_id)
    crud.calcular_percentual_carteira(db, carteira_id)

    # Recarrega o objeto para obter os valores atualizados
    db_carteira = crud.get_carteira(db, carteira_id=carteira_id)

    return db_carteira


@router.get(
    "/",
    response_model=List[schemas.Carteira],
    summary="Lista todas as carteiras"
)
def get_all_wallets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retorna uma lista de todas as carteiras ativas.
    """
    carteiras = crud.get_carteiras(db, skip=skip, limit=limit)
    return carteiras


@router.delete(
    "/{carteira_id}",
    response_model=schemas.ResponseMessage,
    summary="Exclui uma carteira (exclusão lógica)"
)
def delete_wallet(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Desativa uma carteira, marcando-a como inativa.
    """
    db_carteira = crud.delete_carteira(db, carteira_id=carteira_id)
    if db_carteira is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")
    return schemas.ResponseMessage(message="Carteira desativada com sucesso.")

# --- Rotas para Ativos na Carteira (CarteiraAtivo) ---


@router.post(
    "/{carteira_id}/ativos",
    response_model=schemas.CarteiraAtivo,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um ativo a uma carteira"
)
def add_asset_to_wallet(
    carteira_id: int,
    carteira_ativo_create: schemas.CarteiraAtivoCreate,
    db: Session = Depends(get_db)
):
    """
    Adiciona um ativo à carteira com dados de quantidade, preço e valor investido.
    """
    db_carteira = crud.get_carteira(db, carteira_id)
    if not db_carteira:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")

    # Garante que o ativo a ser adicionado pertence à carteira correta
    carteira_ativo_create.carteira_id = carteira_id

    db_carteira_ativo = crud.get_carteira_ativo(
        db, carteira_id, carteira_ativo_create.ativo_id)
    if db_carteira_ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ativo já existe nesta carteira. Use o endpoint de transação para adicionar mais.")

    return crud.create_carteira_ativo(db, carteira_ativo=carteira_ativo_create)


@router.get(
    "/{carteira_id}/ativos",
    response_model=List[schemas.CarteiraAtivo],
    summary="Lista os ativos de uma carteira"
)
def get_assets_in_wallet(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de todos os ativos em uma carteira específica.
    """
    db_carteira = crud.get_carteira(db, carteira_id)
    if not db_carteira:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")

    return crud.get_carteira_ativos(db, carteira_id)


@router.delete(
    "/ativos/{carteira_ativo_id}",
    response_model=schemas.ResponseMessage,
    summary="Remove um ativo de uma carteira"
)
def remove_asset_from_wallet(
    carteira_ativo_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove um ativo de uma carteira específica.
    """
    success = crud.delete_carteira_ativo(db, carteira_ativo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ativo na carteira não encontrado")

    return schemas.ResponseMessage(message="Ativo removido da carteira com sucesso.", success=True)

# --- Rotas para Transações ---


@router.post(
    "/{carteira_id}/transacoes",
    response_model=schemas.Transacao,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma nova transação"
)
def create_transaction(
    carteira_id: int,
    transacao_create: schemas.TransacaoCreate,
    db: Session = Depends(get_db)
):
    """
    Registra uma transação (compra ou venda) em uma carteira.

    - **Atenção**: Esta rota é apenas para registro. A lógica para atualizar a carteira
      (quantidade, preço médio, valor investido) deve ser implementada em um serviço
      dedicado que usa essa transação para recalcular os valores da carteira.
    """
    db_carteira = crud.get_carteira(db, carteira_id)
    if not db_carteira:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")

    transacao_create.carteira_id = carteira_id

    return crud.create_transacao(db, transacao=transacao_create)


@router.get(
    "/{carteira_id}/transacoes",
    response_model=List[schemas.Transacao],
    summary="Lista as transações de uma carteira"
)
def get_transactions(
    carteira_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de transações de uma carteira.
    """
    db_carteira = crud.get_carteira(db, carteira_id)
    if not db_carteira:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Carteira não encontrada")

    return crud.get_transacoes(db, carteira_id=carteira_id)
