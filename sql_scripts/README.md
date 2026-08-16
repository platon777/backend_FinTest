# SQL scripts historiques

Les anciens scripts de ce dossier ciblaient SQL Server/Azure et ne sont plus utilisés par le backend refactoré. Le schéma PostgreSQL du prototype est défini par les modèles SQLAlchemy et la migration `alembic/versions/0001_core_schema.py`, puis chargé par `scripts/seed.py`.
