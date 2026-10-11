# 02 - MCD, MLD, MPD

## MCD: vue conceptuelle

Le domaine est organise autour du vin.

- Un `wine` est produit par un `winery` et rattache a une `region`.
- Un `wine` possede plusieurs `vintages` (millesimes).
- Un `vintage` peut recevoir plusieurs `price_offers` chez plusieurs `merchants`.
- Un `vintage` peut recevoir plusieurs notes de `critics`.
- Un `wine` peut etre compose de plusieurs `grapes`.
- Un `wine` peut etre associe a plusieurs `foods`.
- Les dimensions `body`, `acidity` et `appellations` decrivent le style du vin.

Cardinalites principales:

| Relation | Cardinalite |
|---|---|
| region -> wineries | 1,N |
| region -> wines | 1,N |
| winery -> wines | 1,N |
| wine -> vintages | 1,N |
| vintage -> price_offers | 1,N |
| merchant -> price_offers | 1,N |
| vintage -> critics | 1,N |
| wine <-> grapes | N,N via `wine_grapes` |
| wine <-> foods | N,N via `wine_food_pairings` |

## MLD: tables logiques

| Table | Cle primaire | Cles etrangeres |
|---|---|---|
| countries | code | - |
| regions | region_id | - |
| wineries | id | region -> regions.region_id |
| wines | wine_id | region_id, winery_id, appelation_id, body_id, acidity_id |
| vintages | id | wine_id -> wines.wine_id |
| price_offers | offer_id | vintage_id, merchant_id |
| merchants | id | - |
| critics | id | vintage_id -> vintages.id |
| grapes | id | - |
| wine_grapes | wine_id + grape_id | wine_id, grape_id |
| foods | id | - |
| wine_food_pairings | wine_id + food_id | wine_id, food_id |
| appellations | id | - |
| body | body_id | - |
| acidity | acidity_id | - |

## MPD: choix physiques SQLite

- SQLite est active avec `PRAGMA foreign_keys = ON`.
- Les identifiants externes Vivino sont conserves comme cles primaires quand ils existent.
- `price_offers.offer_id` est une cle technique, car le fichier de prix n'a pas de cle primaire.
- Les tables de jointure ont une cle primaire composee pour bloquer les doublons.
- Des index sont poses sur les principales cles etrangeres pour accelerer les jointures.
- Les types restent volontairement simples: `INTEGER`, `REAL`, `TEXT`.

Le script SQL physique complet est dans `schema.sql`.
