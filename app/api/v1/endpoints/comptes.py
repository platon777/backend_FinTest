"""
Endpoints pour la gestion des Comptes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.comptes import *
from app.services.comptes_service import ComptesService

router = APIRouter()


@router.post("/", response_model=CompteCreateResponse, status_code=status.HTTP_201_CREATED)
def creer_compte(
    data: CompteCreate,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Créer un nouveau compte d'investissement"""
    try:
        # Seul le client peut créer un compte pour lui-même dans cette version
        if data.ClientID != current_client.ClientID:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez créer un compte que pour vous-même"
            )

        compte = ComptesService.creer_compte(
            db=db,
            client_id=data.ClientID,
            numero_compte=data.NumeroCompte,
            type_compte=data.TypeCompte,
            devise=data.Devise,
            role=data.Role
        )

        return CompteCreateResponse(
            success=True,
            message="Compte créé avec succès",
            compte=CompteResponse.from_orm(compte)
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/mes-comptes", response_model=ComptesListResponse)
def get_mes_comptes(
    statut: Optional[str] = None,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer tous les comptes du client connecté"""
    try:
        comptes = ComptesService.get_comptes_client(db, current_client.ClientID, statut)
        return ComptesListResponse(
            total=len(comptes),
            comptes=[CompteResponse.from_orm(c) for c in comptes]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{compte_id}", response_model=CompteDetail)
def get_compte(
    compte_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer les détails d'un compte"""
    try:
        # Vérifier l'accès
        if not ComptesService.verifier_acces_compte(db, compte_id, current_client.ClientID):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé à ce compte"
            )

        compte = ComptesService.get_compte_by_id(db, compte_id)
        if not compte:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")

        return CompteDetail.from_orm(compte)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{compte_id}/suspendre", response_model=CompteResponse)
def suspendre_compte(
    compte_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Suspendre un compte"""
    try:
        # Vérifier que le client est titulaire principal
        if not ComptesService.verifier_role_compte(
            db, compte_id, current_client.ClientID, ['TITULAIRE_PRINCIPAL']
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le titulaire principal peut suspendre le compte"
            )

        compte = ComptesService.suspendre_compte(db, compte_id)
        return CompteResponse.from_orm(compte)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{compte_id}", response_model=CompteResponse)
def fermer_compte(
    compte_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Fermer un compte (solde doit être 0)"""
    try:
        if not ComptesService.verifier_role_compte(
            db, compte_id, current_client.ClientID, ['TITULAIRE_PRINCIPAL']
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le titulaire principal peut fermer le compte"
            )

        compte = ComptesService.fermer_compte(db, compte_id)
        return CompteResponse.from_orm(compte)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
