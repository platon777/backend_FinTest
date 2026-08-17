# Comptes de démonstration ProFin

Ces comptes sont réservés au prototype local Docker et ne doivent pas être réutilisés en production.

Mot de passe commun : `ProfinDemo!2026`

| Compte | Email | Profil | Données métier |
|---|---|---|---|
| Marie Jean | `marie.jean@demo.profin.ht` | Individuel, risque modéré | USD `INV-2026-00001`, HTG `SVG-2026-00002`, obligations BRH 2027 et EDH 2028 |
| Caribe Investissements S.A. | `caribe.invest@demo.profin.ht` | Institutionnel, risque agressif | USD `INV-2026-00004`, fonds Croissance Caraïbes, KYC institutionnel |
| Paul Joseph | `paul.observer@demo.profin.ht` | Individuel, conservateur | Rôle `OBSERVATEUR` sur `JNT-2026-00003`; consultation seule |
| Sophie Laurent | `sophie.checker@demo.profin.ht` | Individuelle, modérée | Rôle `MANDATAIRE` sur `INV-2026-00001`; profil de validation |
| Nadia Bernard | `nadia.checker@demo.profin.ht` | Individuelle, modérée | Rôle `MANDATAIRE` sur le compte Marie; peut traiter une correction après sa création |
| Nexa Patrimoine S.A. | `nexa.patrimoine@demo.profin.ht` | Institutionnel, trésorerie | USD `INV-2026-00005`, HTG `TRE-2026-00006`, position Caraïbes 2029 et opérations en attente/rejetées |
| Julien Bernard | `julien.bernard@demo.profin.ht` | Individuel, conservateur | USD `INV-2026-00007`, obligation BRH 2027, coupon en attente; Sophie est mandataire et Paul observateur |
| Aline Michel | `aline.michel@demo.profin.ht` | Individuelle, modérée | USD `INV-2026-00008`, obligation EDH 2028, coupon planifié; Sophie est mandataire |

## Parcours de présentation

### Marie — portefeuille multi-devises

Le dashboard montre deux positions obligataires :

- Obligation BRH 2027 : 20 000 USD investis, valeur actuelle 21 100 USD;
- Obligation Énergie EDH 2028 : 15 000 USD investis, valeur actuelle 15 586 USD.

Les liquidités sont présentées séparément : 25 000 USD disponibles après réservation de l'ordre de démonstration et 605 000 HTG répartis sur les comptes rattachés.

### Ordre d'investissement et maker/checker

Marie dispose d'un ordre BRH 2027 en `SUBMITTED` pour 10 000 USD. Le montant est réservé dans le disponible, mais aucun débit comptable ni position n'est créé à la soumission.

1. Connecter Marie et ouvrir `Investir` pour consulter l'ordre et ses trois étapes.
2. Se connecter avec Sophie, qui partage le compte comme `MANDATAIRE`.
3. Approuver successivement `CONFORMITE`, `BACK_OFFICE`, puis `CHECKER`.
4. Contrôler la création de la position, de la transaction `SOUSCRIPTION` et des deux écritures comptables.

Le maker ne peut pas valider son propre ordre. Un rejet libère le montant réservé sans modifier le solde comptable.

### Caribe — client institutionnel

Le compte institutionnel contient 150 000 USD disponibles et une position de 100 000 USD dans le fonds `FND-CARAIBE-2030`, valorisée à 104 700 USD.

Un ordre de réallocation de 30 000 USD est déjà au stade `BACK_OFFICE_REVIEW`, avec la conformité approuvée et les contrôles opérationnels et finaux encore à traiter.

### Nexa — entreprise multi-comptes

Nexa Patrimoine représente une seconde entreprise avec deux comptes de nature différente : un compte d'investissement USD et un compte de trésorerie HTG. Son compte USD porte une obligation Caraïbes 2029 de 75 000 USD, avec une valeur actuelle de 76 200 USD.

- Sophie a le rôle `MANDATAIRE` sur le compte USD et peut traiter la file de validation;
- Paul a le rôle `OBSERVATEUR` sur le compte USD et peut consulter sans agir;
- Nadia a le rôle `MANDATAIRE` sur le compte HTG;
- un retrait USD de 25 000 est en attente de validation;
- un retrait de 12 000 USD est rejeté avec un motif de justificatif manquant;
- un ordre de 50 000 USD est rejeté pour allocation hors mandat.

Ce cas permet de montrer que les habilitations sont attachées au compte, pas seulement à la personne, et que chaque décision conserve son motif.

### Paul — observateur

Paul peut consulter le compte joint HTG, mais son rôle `OBSERVATEUR` ne lui permet pas de créer ou valider un mouvement.

### Echeance proche

Marie dispose aussi de `OBL-BRH-2026`, une position de 5 000 USD arrivant a echeance dans 60 jours. Elle permet de montrer le suivi des echeances depuis le rapport client, puis le traitement de la demande de remboursement depuis le pilotage habilite.

### Rendement, coupons et frais

Le portefeuille Marie porte un rendement annualise calcule sur les flux dates, des frais d'entree par instrument et des coupons BRH. Les positions affichent aussi les interets courus : ils sont acquis selon le temps de detention, mais ne sont pas encore necessairement verses sur le compte.

Le jeu de donnees permet de montrer plusieurs etats :

- Marie : coupons BRH 2027 deja payes, coupon EDH 2028 planifie et coupon BRH 2026 planifie avant une echeance proche;
- Julien : coupon BRH 2027 de 275 USD en attente de validation;
- Aline : coupon EDH 2028 de 1 125 USD planifie;
- Nexa : coupon Caraibes 2029 de 5 175 USD planifie, visible par Paul en consultation seule.

Ainsi, le total des interets courus n'est pas confondu avec le solde disponible : le premier represente un revenu accumule sur les positions, tandis que le second represente l'argent utilisable immediatement.

### Correction comptable

Une transaction executee peut etre selectionnee pour une contrepassation. La correction cree une nouvelle operation soumise au controle, conserve l'operation d'origine et ajoute une version comptable inversee.

Le jeu de données contient un frais de tenue de compte de 125 USD sur Marie, ainsi qu'une contrepassation demandée par Sophie. Nadia peut ensuite reprendre la demande pour illustrer la séparation entre la personne qui crée la correction et celle qui la valide.

## Exemple de connexion

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"marie.jean@demo.profin.ht","password":"ProfinDemo!2026"}'
```
