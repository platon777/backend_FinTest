# Comptes de démonstration ProFin

Ces comptes sont réservés au prototype local Docker et ne doivent pas être réutilisés en production.

Mot de passe commun : `ProfinDemo!2026`

| Compte | Email | Profil | Données métier |
|---|---|---|---|
| Marie Jean | `marie.jean@demo.profin.ht` | Individuel, risque modéré | USD `INV-2026-00001`, HTG `SVG-2026-00002`, obligations BRH 2027 et EDH 2028 |
| Caribe Investissements S.A. | `caribe.invest@demo.profin.ht` | Institutionnel, risque agressif | USD `INV-2026-00004`, fonds Croissance Caraïbes, KYC institutionnel |
| Paul Joseph | `paul.observer@demo.profin.ht` | Individuel, conservateur | Rôle `OBSERVATEUR` sur `JNT-2026-00003`; consultation seule |
| Sophie Laurent | `sophie.checker@demo.profin.ht` | Individuelle, modérée | Rôle `MANDATAIRE` sur `INV-2026-00001`; profil de validation |

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

### Paul — observateur

Paul peut consulter le compte joint HTG, mais son rôle `OBSERVATEUR` ne lui permet pas de créer ou valider un mouvement.

## Exemple de connexion

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"marie.jean@demo.profin.ht","password":"ProfinDemo!2026"}'
```
