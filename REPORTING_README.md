# Reporting métier ProFin

Le reporting est une lecture dérivée du modèle transactionnel. Il ne modifie
jamais les comptes, les positions ou les écritures comptables.

## Vues PostgreSQL

- `vw_reporting_client_positions` : positions actives par client, compte,
  devise et instrument;
- `vw_reporting_order_pipeline` : état d'un ordre, prochaine étape et âge de
  la demande;
- `vw_reporting_transaction_queue` : mouvements en attente de validation;
- `profin_order_next_step(integer)` : fonction SQL qui détermine l'étape
  suivante dans l'ordre conformité, traitement opérationnel, validation finale.

Les objets sont créés par la migration Alembic `0003_reporting_views`.

## API

- `GET /api/v1/dashboard/rapports/client` : synthèse multi-devises, allocation,
  échéances à 90 jours, flux exécutés et demandes en cours;
- `GET /api/v1/dashboard/rapports/back-office` : indicateurs, file de travail,
  ancienneté, périmètre de comptes et points de vigilance.

Le second rapport est refusé au serveur pour un profil qui ne possède pas une
habilitation active de type `MANDATAIRE`, `CONFORMITE`, `BACK_OFFICE` ou
`SUPERVISEUR`.

## Règle de lecture

Les montants ne sont jamais additionnés entre USD et HTG. Chaque agrégat porte
sa devise, afin d'éviter de présenter un faux total consolidé sans taux de
change explicite.
