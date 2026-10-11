# 04 - Hypotheses nulles exploratoires

Ces hypotheses servent d'exercice analytique apres integration. Elles ne prouvent pas une causalite; elles donnent un cadre propre pour interroger la base.

## H0-1: le pays ne change pas le prix median

Hypothese nulle: la distribution du prix median est identique entre deux pays compares.

Premier repere observe dans l'export:

| Pays | Prix median |
|---|---:|
| Chili | 138.33 |
| États-Unis | 85.00 |
| Australie | 50.84 |
| France | 48.38 |
| Italie | 41.67 |
| Argentine | 31.41 |
| Nouvelle-Zélande | 30.67 |
| Espagne | 28.45 |

Test possible: permutation ou bootstrap sur `median_price` par pays.

## H0-2: la note moyenne n'est pas correlee au prix

Hypothese nulle: `ratings_average` et `price` sont independants.

Dans SQLite, on joint `price_offers -> vintages`. En pandas, on peut calculer une correlation de Spearman puis la comparer a une distribution permutee.

## H0-3: les vins mono-cepage et multi-cepages ont le meme prix

Hypothese nulle: le nombre de cepages d'un vin ne change pas son prix median.

Construction:

1. compter les cepages par `wine_id` dans `wine_grapes`;
2. separer `nb_grapes = 1` et `nb_grapes > 1`;
3. comparer `median_price` via permutation.
