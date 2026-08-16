# Comptes de démonstration ProFin

Ces comptes sont uniquement destinés au prototype local Docker. Ils ne doivent pas être réutilisés en production.

Mot de passe commun : `ProfinDemo!2026`

| Compte | Email | Profil | Données métier |
|---|---|---|---|
| Marie Jean | `marie.jean@demo.profin.ht` | Individuel, risque modéré | USD `INV-2026-00001`, HTG `SVG-2026-00002`, obligations BRH 2027 et EDH 2028, adresse et téléphone KYC |
| Caribe Investissements S.A. | `caribe.invest@demo.profin.ht` | Institutionnel, risque agressif | USD `INV-2026-00004`, fonds Croissance Caraïbes, représentant légal et registre de commerce |
| Paul Joseph | `paul.observer@demo.profin.ht` | Individuel, conservateur | Rôle `OBSERVATEUR` sur `JNT-2026-00003`; consultation autorisée, opérations interdites |

## Scénarios de vérification

### Marie

Après connexion, le dashboard montre deux positions obligataires :

- Obligation BRH 2027 : 20 000 USD investis, valeur actuelle 21 100 USD;
- Obligation Énergie EDH 2028 : 15 000 USD investis, valeur actuelle 15 586 USD.

Le compte USD conserve 35 000 USD disponibles et l'épargne HTG 420 000 HTG. Une nouvelle transaction cash est créée en `PENDING_APPROVAL`.

### Caribe Investissements

Le compte institutionnel contient 150 000 USD disponibles et une position de 100 000 USD dans le fonds `FND-CARAIBE-2030`, valorisée à 104 700 USD.

### Maker/checker

Pour tester ce parcours avec le jeu de données de test, créer une opération depuis un maker puis la valider avec un autre titulaire autorisé. Le même client ne peut pas valider sa propre transaction. Les tests automatisés couvrent ce comportement.

## Exemple de connexion

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"marie.jean@demo.profin.ht","password":"ProfinDemo!2026"}'
```
