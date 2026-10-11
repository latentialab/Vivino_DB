# 01 - Nettoyage et audit des donnees

Objectif: partir des CSV bruts, documenter les anomalies, puis produire des tables propres pour SQLite.

## Inventaire des fichiers

| Fichier | Lignes | Colonnes | Doublons exacts |
|---|---:|---:|---:|
| `acidity_df.csv` | 3 | 2 | 0 |
| `appelations.csv` | 75 | 6 | 0 |
| `body_df.csv` | 4 | 2 | 0 |
| `countries_df.csv` | 12 | 7 | 0 |
| `critics_df.csv` | 5796 | 4 | 0 |
| `grapes_df.csv` | 119 | 3 | 0 |
| `meat_info_df.csv` | 21 | 3 | 0 |
| `meat_wine_df.csv` | 3146 | 2 | 0 |
| `merchants_df.csv` | 334 | 4 | 0 |
| `prices.csv` | 13350 | 8 | 0 |
| `regions_df.csv` | 214 | 3 | 0 |
| `vintages.csv` | 29671 | 9 | 0 |
| `wineries.csv` | 524 | 13 | 0 |
| `wine_df_fin.csv` | 3600 | 43 | 1571 |
| `wine_grapes_df.csv` | 2082 | 3 | 0 |

## Points d'attention reperes

- `wine_df_fin.csv`: 3600 lignes pour 794 vins et 2023 millesimes; 1571 doublons exacts.
- `vintages.csv`: 29671 lignes, 29635 identifiants de millesime; 36 doublons sur la cle `id`.
- `regions_df.csv`: 1 ligne sans `region_id`, retiree avant insertion.
- `wineries.csv`: 38 regions referencees par des domaines etaient absentes du referentiel; des lignes techniques `Region inconnue <id>` ont ete ajoutees.
- `prices.csv`: 13350 offres, prix entre 3.75 et 820.00 EUR.
- `appelations.csv`: 32 identifiants references par `wine_df_fin.csv` etaient absents du referentiel; des lignes techniques `Appellation inconnue <id>` ont ete ajoutees pour conserver l'integrite referentielle.

## Valeurs nulles principales

| Table brute | Colonne | Nulls | Taux |
|---|---|---:|---:|
| `meat_info_df.csv` | `seo_name` | 12 | 57.1% |
| `merchants_df.csv` | `url` | 295 | 88.3% |
| `prices.csv` | `bottles_sold` | 12498 | 93.6% |
| `prices.csv` | `bottles_in_stock` | 9768 | 73.2% |
| `prices.csv` | `message` | 7219 | 54.1% |
| `regions_df.csv` | `region_id` | 1 | 0.5% |
| `regions_df.csv` | `name_en` | 1 | 0.5% |
| `regions_df.csv` | `country` | 1 | 0.5% |
| `wineries.csv` | `winemaker` | 192 | 36.6% |
| `wineries.csv` | `email` | 149 | 28.4% |
| `wineries.csv` | `longitude` | 140 | 26.7% |
| `wineries.csv` | `latitude` | 140 | 26.7% |
| `wineries.csv` | `phone` | 61 | 11.6% |
| `wineries.csv` | `website` | 59 | 11.3% |
| `wine_df_fin.csv` | `closure` | 3404 | 94.6% |
| `wine_df_fin.csv` | `certified_biodynamic` | 3051 | 84.8% |
| `wine_df_fin.csv` | `contains_milk_allergens` | 2489 | 69.1% |
| `wine_df_fin.csv` | `contains_egg_allergens` | 2489 | 69.1% |
| `wine_df_fin.csv` | `contains_added_sulfites` | 2229 | 61.9% |
| `wine_df_fin.csv` | `wine_description` | 1461 | 40.6% |
| `wine_df_fin.csv` | `alcohol` | 614 | 17.1% |
| `wine_df_fin.csv` | `acidity_id` | 41 | 1.1% |

## Distributions utiles

| Indicateur | Min | Q1 | Mediane | Q3 | Max |
|---|---:|---:|---:|---:|---:|
| Prix des offres | 3.75 | 34.50 | 61.49 | 113.40 | 820.00 |
| Note moyenne des millesimes | 0.00 | 0.00 | 3.80 | 4.10 | 4.90 |
| Nombre d'avis des millesimes | 1.00 | 4.00 | 30.00 | 292.00 | 142572.00 |
| Alcool des vins | 8.50 | 13.00 | 13.50 | 14.00 | 16.50 |
| Prix median export | 7.25 | 24.31 | 39.17 | 88.22 | 354.00 |

## Regles de nettoyage appliquees

1. Suppression des doublons exacts de l'export vin.
2. Conservation d'une seule ligne par cle primaire dans les referentiels.
3. Dedoublonnage des millesimes sur `id`, en gardant la ligne la plus complete en compte de notes/avis.
4. Separation des entites: vin, millesime, offre de prix, marchand, critique, region, domaine, cepage et accord mets.
5. Creation d'une cle technique `offer_id` pour les offres de prix, car le CSV n'a pas d'identifiant stable.
6. Ajout de lignes techniques pour les regions et appellations manquantes afin d'activer les contraintes de cle etrangere.

## Resultat apres nettoyage

| Table SQLite | Lignes |
|---|---:|
| `countries` | 12 |
| `regions` | 251 |
| `appellations` | 107 |
| `body` | 4 |
| `acidity` | 3 |
| `grapes` | 119 |
| `foods` | 21 |
| `merchants` | 334 |
| `wineries` | 524 |
| `wines` | 794 |
| `vintages` | 29635 |
| `wine_grapes` | 1514 |
| `wine_food_pairings` | 3146 |
| `price_offers` | 13350 |
| `critics` | 5796 |
