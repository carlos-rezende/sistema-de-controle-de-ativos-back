import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv
from typing import Iterator

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. Configuração do Engine e da Sessão ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ativos.db")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    """
    Função geradora para obter uma sessão de banco de dados.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    Cria todas as tabelas definidas nos modelos no banco de dados.
    """
    from .models import Base as ModelsBase
    print("Criando tabelas no banco de dados...")
    ModelsBase.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")


def init_db():
    """
    Inicializa o banco de dados, criando apenas as tabelas.
    Nenhum dado inicial é inserido.
    """
    create_all_tables()


if __name__ == "__main__":
    init_db()
