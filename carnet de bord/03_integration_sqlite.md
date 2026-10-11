# 03 - Integration CSV vers SQLite

## Etape 1: lire les CSV

Tous les fichiers source restent dans `vivino/`. Le carnet ne modifie pas les CSV originaux.

```powershell
python "carnet de bord/scripts/build_carnet.py"
```

## Etape 2: nettoyer

Le script applique les regles suivantes:

- retrait de la ligne region vide;
- dedoublonnage des referentiels par cle;
- dedoublonnage des millesimes par `id`;
- separation de `wine_df_fin.csv` en entites `wines` et enrichissement `vintages`;
- creation de `offer_id` pour les prix;
- ajout des appellations manquantes sous forme de stubs documentes.

## Etape 3: construire les tables

Le fichier `schema.sql` detruit/recree les tables dans l'ordre, puis le script insere les donnees dans l'ordre des dependances.

## Etape 4: verifier

Le script lance `PRAGMA foreign_key_check`. Si une relation est invalide, l'execution echoue.

Commandes utiles:

```powershell
python -c "import sqlite3; c=sqlite3.connect('carnet de bord/vivino.sqlite'); print(c.execute('select count(*) from wines').fetchone())"
python -c "import sqlite3; c=sqlite3.connect('carnet de bord/vivino.sqlite'); print(c.execute('pragma foreign_key_check').fetchall())"
```

## Exemple de requete

```sql
SELECT w.country, ROUND(AVG(p.price), 2) AS prix_moyen, COUNT(*) AS nb_offres
FROM price_offers p
JOIN vintages v ON v.id = p.vintage_id
JOIN wines w ON w.wine_id = v.wine_id
GROUP BY w.country
ORDER BY prix_moyen DESC;
```
