from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

# URL do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ativos.db")

# Cria o engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Cria a sessão do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

def get_db():
    """Função para obter uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Cria todas as tabelas no banco de dados"""
    from models import Base
    Base.metadata.create_all(bind=engine)

def init_db():
    """Inicializa o banco de dados com dados básicos"""
    create_tables()
    
    # Aqui podemos adicionar dados iniciais se necessário
    db = SessionLocal()
    try:
        # Exemplo: inserir alguns ativos básicos
        from models import Ativo
        
        # Verifica se já existem ativos
        existing_ativos = db.query(Ativo).count()
        if existing_ativos == 0:
            # Adiciona alguns ativos de exemplo
            ativos_exemplo = [
                Ativo(
                    ticker="PETR4",
                    nome_curto="PETROBRAS PN",
                    nome_longo="Petróleo Brasileiro S.A. - Petrobras",
                    tipo="ACAO",
                    setor="Petróleo, Gás e Biocombustíveis"
                ),
                Ativo(
                    ticker="VALE3",
                    nome_curto="VALE ON",
                    nome_longo="Vale S.A.",
                    tipo="ACAO",
                    setor="Mineração"
                ),
                Ativo(
                    ticker="ITUB4",
                    nome_curto="ITAUUNIBANCO PN",
                    nome_longo="Itaú Unibanco Holding S.A.",
                    tipo="ACAO",
                    setor="Bancos"
                ),
                Ativo(
                    ticker="MGLU3",
                    nome_curto="MAGAZ LUIZA ON",
                    nome_longo="Magazine Luiza S.A.",
                    tipo="ACAO",
                    setor="Comércio"
                ),
                Ativo(
                    ticker="HGLG11",
                    nome_curto="CSHG LOGÍSTICA",
                    nome_longo="CSHG Logística Fundo de Investimento Imobiliário",
                    tipo="FII",
                    setor="Logística"
                ),
                Ativo(
                    ticker="XPML11",
                    nome_curto="XP MALLS",
                    nome_longo="XP Malls Fundo de Investimento Imobiliário",
                    tipo="FII",
                    setor="Shopping Centers"
                )
            ]
            
            for ativo in ativos_exemplo:
                db.add(ativo)
            
            db.commit()
            print("Dados iniciais inseridos no banco de dados.")
        
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

