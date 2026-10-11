from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vivino"
OUT = ROOT / "carnet de bord"
DB_PATH = OUT / "vivino.sqlite"
SCHEMA_PATH = OUT / "schema.sql"


CSV_TABLES = {
    "acidity": "acidity_df.csv",
    "appellations": "appelations.csv",
    "body": "body_df.csv",
    "countries": "countries_df.csv",
    "critics": "critics_df.csv",
    "grapes": "grapes_df.csv",
    "foods": "meat_info_df.csv",
    "wine_food_pairings": "meat_wine_df.csv",
    "merchants": "merchants_df.csv",
    "price_offers_raw": "prices.csv",
    "regions": "regions_df.csv",
    "vintages_raw": "vintages.csv",
    "wineries": "wineries.csv",
    "wine_export": "wine_df_fin.csv",
    "wine_grapes": "wine_grapes_df.csv",
}


def load_csvs() -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(SOURCE / file_name) for name, file_name in CSV_TABLES.items()}


def dedupe_by_key(df: pd.DataFrame, key: str, sort_cols: list[str] | None = None) -> pd.DataFrame:
    work = df.copy()
    if sort_cols:
        existing = [col for col in sort_cols if col in work.columns]
        if existing:
            work = work.sort_values(existing)
    return work.drop_duplicates(subset=[key], keep="last").reset_index(drop=True)


def clean_tables(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}

    tables["countries"] = raw["countries"].drop_duplicates("code").copy()
    regions = raw["regions"].dropna(subset=["region_id"]).drop_duplicates("region_id").copy()
    missing_winery_regions = sorted(
        set(raw["wineries"]["region"].dropna().astype(int)) - set(regions["region_id"].dropna().astype(int))
    )
    if missing_winery_regions:
        region_stubs = pd.DataFrame(
            {
                "region_id": missing_winery_regions,
                "name_en": [f"Region inconnue {region_id}" for region_id in missing_winery_regions],
                "country": [None] * len(missing_winery_regions),
            }
        )
        regions = pd.concat([regions, region_stubs], ignore_index=True)
    tables["regions"] = regions
    tables["body"] = raw["body"].drop_duplicates("body_id").copy()
    tables["acidity"] = raw["acidity"].drop_duplicates("acidity_id").copy()
    tables["grapes"] = raw["grapes"].drop_duplicates("id").copy()
    tables["foods"] = raw["foods"].drop_duplicates("id").copy()
    tables["merchants"] = raw["merchants"].drop_duplicates("id").copy()
    tables["wineries"] = raw["wineries"].drop_duplicates("id").copy()

    wine_export = raw["wine_export"].drop_duplicates().copy()
    wine_export["ratings_total"] = wine_export[
        [
            "ratings_distribution_1",
            "ratings_distribution_2",
            "ratings_distribution_3",
            "ratings_distribution_4",
            "ratings_distribution_5",
        ]
    ].sum(axis=1)

    appellations = raw["appellations"].drop_duplicates("id").copy()
    missing_app_ids = sorted(
        set(wine_export["appelation_id"].dropna().astype(int)) - set(appellations["id"].astype(int))
    )
    if missing_app_ids:
        stubs = pd.DataFrame(
            {
                "id": missing_app_ids,
                "regional_name": [None] * len(missing_app_ids),
                "name": [f"Appellation inconnue {app_id}" for app_id in missing_app_ids],
                "description": [None] * len(missing_app_ids),
                "interesting_facts": [None] * len(missing_app_ids),
                "country": [None] * len(missing_app_ids),
            }
        )
        appellations = pd.concat([appellations, stubs], ignore_index=True)
    tables["appellations"] = appellations

    wine_sort = ["wine_id", "ratings_total", "median_price"]
    wine_columns = [
        "wine_id",
        "wine_name",
        "type",
        "is_natural",
        "certified_biodynamic",
        "region_id",
        "country",
        "winery_id",
        "rank_percentile_country",
        "rank_percentile_region",
        "rank_percentile_winery",
        "rank_percentile_wine_type",
        "rank_percentile_global",
        "wine_description",
        "alcohol",
        "appelation_id",
        "body_id",
        "acidity_id",
        "awards_number",
        "awards_bronze_number",
        "awards_silver_number",
        "awards_gold_number",
        "awards_excellent_number",
        "awards_platinum_number",
        "awards_remarkable_number",
        "awards_commended_number",
        "ratings_distribution_1",
        "ratings_distribution_2",
        "ratings_distribution_3",
        "ratings_distribution_4",
        "ratings_distribution_5",
        "contains_added_sulfites",
        "contains_milk_allergens",
        "contains_egg_allergens",
        "closure",
    ]
    tables["wines"] = (
        wine_export.sort_values(wine_sort)
        .drop_duplicates("wine_id", keep="last")[wine_columns]
        .reset_index(drop=True)
    )

    vintages = raw["vintages_raw"].copy()
    vintages = dedupe_by_key(vintages, "id", ["id", "ratings_count", "reviews_count"])
    wine_prices = (
        wine_export.groupby("vintage_id", as_index=False)
        .agg(
            export_name=("name", "first"),
            export_year=("year", "max"),
            median_price=("median_price", "median"),
            vintage_rank_percentile_country=("vintage_rank_percentile_country", "min"),
            vintage_rank_percentile_region=("vintage_rank_percentile_region", "min"),
            vintage_rank_percentile_winery=("vintage_rank_percentile_winery", "min"),
            vintage_rank_percentile_global=("vintage_rank_percentile_global", "min"),
        )
        .rename(columns={"vintage_id": "id"})
    )
    tables["vintages"] = vintages.merge(wine_prices, on="id", how="left")

    tables["wine_grapes"] = raw["wine_grapes"].drop_duplicates(["wine_id", "grape_id"]).copy()
    tables["wine_food_pairings"] = raw["wine_food_pairings"].drop_duplicates(["wine_id", "food_id"]).copy()
    tables["critics"] = raw["critics"].drop_duplicates("id").copy()

    offers = raw["price_offers_raw"].drop_duplicates().copy().reset_index(drop=True)
    offers.insert(0, "offer_id", np.arange(1, len(offers) + 1))
    tables["price_offers"] = offers

    return tables


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS critics;
DROP TABLE IF EXISTS price_offers;
DROP TABLE IF EXISTS wine_food_pairings;
DROP TABLE IF EXISTS wine_grapes;
DROP TABLE IF EXISTS vintages;
DROP TABLE IF EXISTS wines;
DROP TABLE IF EXISTS wineries;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS appellations;
DROP TABLE IF EXISTS acidity;
DROP TABLE IF EXISTS body;
DROP TABLE IF EXISTS grapes;
DROP TABLE IF EXISTS foods;
DROP TABLE IF EXISTS merchants;

CREATE TABLE countries (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    currency TEXT,
    regions_count REAL,
    users_count REAL,
    wines_count REAL,
    wineries_count REAL
);

CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    country TEXT
);

CREATE TABLE appellations (
    id INTEGER PRIMARY KEY,
    regional_name TEXT,
    name TEXT NOT NULL,
    description TEXT,
    interesting_facts TEXT,
    country TEXT
);

CREATE TABLE body (
    body_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE acidity (
    acidity_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE grapes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    wines_count INTEGER
);

CREATE TABLE foods (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    seo_name TEXT
);

CREATE TABLE merchants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    payments TEXT
);

CREATE TABLE wineries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    review_status TEXT,
    average_rating REAL,
    number_of_wines INTEGER,
    region INTEGER,
    business_name TEXT,
    phone TEXT,
    email TEXT,
    winemaker TEXT,
    website TEXT,
    latitude REAL,
    longitude REAL,
    FOREIGN KEY(region) REFERENCES regions(region_id)
);

CREATE TABLE wines (
    wine_id INTEGER PRIMARY KEY,
    wine_name TEXT NOT NULL,
    type TEXT,
    is_natural INTEGER,
    certified_biodynamic INTEGER,
    region_id INTEGER,
    country TEXT,
    winery_id INTEGER,
    rank_percentile_country REAL,
    rank_percentile_region REAL,
    rank_percentile_winery REAL,
    rank_percentile_wine_type REAL,
    rank_percentile_global REAL,
    wine_description TEXT,
    alcohol REAL,
    appelation_id INTEGER,
    body_id INTEGER,
    acidity_id INTEGER,
    awards_number INTEGER,
    awards_bronze_number INTEGER,
    awards_silver_number INTEGER,
    awards_gold_number INTEGER,
    awards_excellent_number INTEGER,
    awards_platinum_number INTEGER,
    awards_remarkable_number INTEGER,
    awards_commended_number INTEGER,
    ratings_distribution_1 INTEGER,
    ratings_distribution_2 INTEGER,
    ratings_distribution_3 INTEGER,
    ratings_distribution_4 INTEGER,
    ratings_distribution_5 INTEGER,
    contains_added_sulfites INTEGER,
    contains_milk_allergens INTEGER,
    contains_egg_allergens INTEGER,
    closure TEXT,
    FOREIGN KEY(region_id) REFERENCES regions(region_id),
    FOREIGN KEY(winery_id) REFERENCES wineries(id),
    FOREIGN KEY(appelation_id) REFERENCES appellations(id),
    FOREIGN KEY(body_id) REFERENCES body(body_id),
    FOREIGN KEY(acidity_id) REFERENCES acidity(acidity_id)
);

CREATE TABLE vintages (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    year TEXT,
    wine_id INTEGER NOT NULL,
    has_valid_ratings INTEGER,
    rating_status TEXT,
    ratings_count INTEGER,
    ratings_average REAL,
    reviews_count INTEGER,
    export_name TEXT,
    export_year REAL,
    median_price REAL,
    vintage_rank_percentile_country REAL,
    vintage_rank_percentile_region REAL,
    vintage_rank_percentile_winery REAL,
    vintage_rank_percentile_global REAL,
    FOREIGN KEY(wine_id) REFERENCES wines(wine_id)
);

CREATE TABLE wine_grapes (
    wine_id INTEGER NOT NULL,
    grape_id INTEGER NOT NULL,
    grapes_share REAL,
    PRIMARY KEY(wine_id, grape_id),
    FOREIGN KEY(wine_id) REFERENCES wines(wine_id),
    FOREIGN KEY(grape_id) REFERENCES grapes(id)
);

CREATE TABLE wine_food_pairings (
    wine_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    PRIMARY KEY(wine_id, food_id),
    FOREIGN KEY(wine_id) REFERENCES wines(wine_id),
    FOREIGN KEY(food_id) REFERENCES foods(id)
);

CREATE TABLE price_offers (
    offer_id INTEGER PRIMARY KEY,
    vintage_id INTEGER NOT NULL,
    merchant_id INTEGER NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    currency TEXT,
    bottles_in_stock REAL,
    bottles_sold REAL,
    message TEXT,
    bottle_volume_ml INTEGER,
    FOREIGN KEY(vintage_id) REFERENCES vintages(id),
    FOREIGN KEY(merchant_id) REFERENCES merchants(id)
);

CREATE TABLE critics (
    id INTEGER PRIMARY KEY,
    score_normalized INTEGER CHECK(score_normalized BETWEEN 0 AND 100),
    reviewed_at TEXT,
    vintage_id INTEGER NOT NULL,
    FOREIGN KEY(vintage_id) REFERENCES vintages(id)
);

CREATE INDEX idx_wines_region ON wines(region_id);
CREATE INDEX idx_wines_winery ON wines(winery_id);
CREATE INDEX idx_vintages_wine ON vintages(wine_id);
CREATE INDEX idx_price_offers_vintage ON price_offers(vintage_id);
CREATE INDEX idx_price_offers_merchant ON price_offers(merchant_id);
CREATE INDEX idx_critics_vintage ON critics(vintage_id);
"""


INSERT_ORDER = [
    "countries",
    "regions",
    "appellations",
    "body",
    "acidity",
    "grapes",
    "foods",
    "merchants",
    "wineries",
    "wines",
    "vintages",
    "wine_grapes",
    "wine_food_pairings",
    "price_offers",
    "critics",
]


def coerce_for_sqlite(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    coerced = {}
    for name, df in tables.items():
        work = df.copy()
        for col in work.columns:
            if work[col].dtype == bool:
                work[col] = work[col].astype("Int64")
        coerced[name] = work.where(pd.notna(work), None)
    return coerced


def build_database(tables: dict[str, pd.DataFrame]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    SCHEMA_PATH.write_text(SCHEMA_SQL.strip() + "\n", encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA_SQL)
        for table in INSERT_ORDER:
            tables[table].to_sql(table, conn, if_exists="append", index=False)
        fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign key errors: {fk_errors[:10]}")
        conn.commit()
    finally:
        conn.close()


def audit_markdown(raw: dict[str, pd.DataFrame], clean: dict[str, pd.DataFrame]) -> str:
    lines = [
        "# 01 - Nettoyage et audit des donnees",
        "",
        "Objectif: partir des CSV bruts, documenter les anomalies, puis produire des tables propres pour SQLite.",
        "",
        "## Inventaire des fichiers",
        "",
        "| Fichier | Lignes | Colonnes | Doublons exacts |",
        "|---|---:|---:|---:|",
    ]
    for name, file_name in CSV_TABLES.items():
        df = raw[name]
        lines.append(f"| `{file_name}` | {len(df)} | {len(df.columns)} | {int(df.duplicated().sum())} |")

    wine = raw["wine_export"]
    vintages = raw["vintages_raw"]
    regions = raw["regions"]
    prices = raw["price_offers_raw"]
    lines += [
        "",
        "## Points d'attention reperes",
        "",
        f"- `wine_df_fin.csv`: {len(wine)} lignes pour {wine['wine_id'].nunique()} vins et {wine['vintage_id'].nunique()} millesimes; {int(wine.duplicated().sum())} doublons exacts.",
        f"- `vintages.csv`: {len(vintages)} lignes, {vintages['id'].nunique()} identifiants de millesime; {int(vintages.duplicated('id').sum())} doublons sur la cle `id`.",
        f"- `regions_df.csv`: {int(regions['region_id'].isna().sum())} ligne sans `region_id`, retiree avant insertion.",
        "- `wineries.csv`: 38 regions referencees par des domaines etaient absentes du referentiel; des lignes techniques `Region inconnue <id>` ont ete ajoutees.",
        f"- `prices.csv`: {len(prices)} offres, prix entre {prices['price'].min():.2f} et {prices['price'].max():.2f} {prices['currency'].mode().iat[0]}.",
        f"- `appelations.csv`: 32 identifiants references par `wine_df_fin.csv` etaient absents du referentiel; des lignes techniques `Appellation inconnue <id>` ont ete ajoutees pour conserver l'integrite referentielle.",
        "",
        "## Valeurs nulles principales",
        "",
        "| Table brute | Colonne | Nulls | Taux |",
        "|---|---|---:|---:|",
    ]
    for name, df in raw.items():
        nulls = df.isna().sum()
        for col, count in nulls[nulls > 0].sort_values(ascending=False).head(8).items():
            lines.append(f"| `{CSV_TABLES[name]}` | `{col}` | {int(count)} | {count / len(df):.1%} |")

    lines += [
        "",
        "## Distributions utiles",
        "",
        "| Indicateur | Min | Q1 | Mediane | Q3 | Max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    distributions = {
        "Prix des offres": prices["price"],
        "Note moyenne des millesimes": vintages["ratings_average"],
        "Nombre d'avis des millesimes": vintages["ratings_count"],
        "Alcool des vins": wine["alcohol"],
        "Prix median export": wine["median_price"],
    }
    for label, series in distributions.items():
        desc = series.dropna().describe(percentiles=[0.25, 0.5, 0.75])
        lines.append(
            f"| {label} | {desc['min']:.2f} | {desc['25%']:.2f} | {desc['50%']:.2f} | {desc['75%']:.2f} | {desc['max']:.2f} |"
        )

    lines += [
        "",
        "## Regles de nettoyage appliquees",
        "",
        "1. Suppression des doublons exacts de l'export vin.",
        "2. Conservation d'une seule ligne par cle primaire dans les referentiels.",
        "3. Dedoublonnage des millesimes sur `id`, en gardant la ligne la plus complete en compte de notes/avis.",
        "4. Separation des entites: vin, millesime, offre de prix, marchand, critique, region, domaine, cepage et accord mets.",
        "5. Creation d'une cle technique `offer_id` pour les offres de prix, car le CSV n'a pas d'identifiant stable.",
        "6. Ajout de lignes techniques pour les regions et appellations manquantes afin d'activer les contraintes de cle etrangere.",
        "",
        "## Resultat apres nettoyage",
        "",
        "| Table SQLite | Lignes |",
        "|---|---:|",
    ]
    for table in INSERT_ORDER:
        lines.append(f"| `{table}` | {len(clean[table])} |")
    return "\n".join(lines) + "\n"


def model_markdown() -> str:
    return """# 02 - MCD, MLD, MPD

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
"""


def integration_markdown() -> str:
    return """# 03 - Integration CSV vers SQLite

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
"""


def hypotheses_markdown(raw: dict[str, pd.DataFrame]) -> str:
    wine = raw["wine_export"].drop_duplicates()
    price_by_country = wine.groupby("country")["median_price"].median().dropna().sort_values(ascending=False)
    return f"""# 04 - Hypotheses nulles exploratoires

Ces hypotheses servent d'exercice analytique apres integration. Elles ne prouvent pas une causalite; elles donnent un cadre propre pour interroger la base.

## H0-1: le pays ne change pas le prix median

Hypothese nulle: la distribution du prix median est identique entre deux pays compares.

Premier repere observe dans l'export:

| Pays | Prix median |
|---|---:|
{chr(10).join(f'| {country} | {value:.2f} |' for country, value in price_by_country.head(8).items())}

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
"""


def readme_markdown() -> str:
    return """# Carnet de bord - Vivino SQLite

Ce dossier contient une version corrigee et reproductible du mini-projet Vivino.

Fichiers principaux:

- `vivino_sqlite_carnet.ipynb`: notebook corrige, oriente SQLite.
- `schema.sql`: MPD executable pour creer les tables.
- `vivino.sqlite`: base SQLite generee.
- `01_audit_nettoyage.md`: audit des erreurs, doublons, nulls, anomalies et distributions.
- `02_mcd_mld_mpd.md`: modele conceptuel, logique et physique.
- `03_integration_sqlite.md`: procedure d'integration CSV -> SQLite.
- `04_hypotheses.md`: 3 hypotheses nulles pour l'analyse.
- `scripts/build_carnet.py`: script qui regenere tout le carnet.

Pour reconstruire la base et les documents:

```powershell
python "carnet de bord/scripts/build_carnet.py"
```

La base produite est `carnet de bord/vivino.sqlite`.
"""


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def markdown_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def notebook() -> dict:
    cells = [
        markdown_cell("# Vivino SQLite - carnet corrige\n\nNotebook de travail pour auditer les CSV, nettoyer les tables, construire le modele MCD/MLD/MPD et interroger une base SQLite."),
        markdown_cell("## 1. Parametres et imports"),
        code_cell("""from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path.cwd()
if ROOT.name == "vivino":
    ROOT = ROOT.parent
SOURCE = ROOT / "vivino"
OUT = ROOT / "carnet de bord"
DB_PATH = OUT / "vivino.sqlite"
print(ROOT)
"""),
        markdown_cell("## 2. Chargement des CSV"),
        code_cell("""csv_files = {
    "acidity": "acidity_df.csv",
    "appellations": "appelations.csv",
    "body": "body_df.csv",
    "countries": "countries_df.csv",
    "critics": "critics_df.csv",
    "grapes": "grapes_df.csv",
    "foods": "meat_info_df.csv",
    "wine_food_pairings": "meat_wine_df.csv",
    "merchants": "merchants_df.csv",
    "price_offers": "prices.csv",
    "regions": "regions_df.csv",
    "vintages": "vintages.csv",
    "wineries": "wineries.csv",
    "wine_export": "wine_df_fin.csv",
    "wine_grapes": "wine_grapes_df.csv",
}

raw = {name: pd.read_csv(SOURCE / file_name) for name, file_name in csv_files.items()}
pd.DataFrame(
    [(name, len(df), len(df.columns), int(df.duplicated().sum())) for name, df in raw.items()],
    columns=["table", "rows", "columns", "exact_duplicates"],
)
"""),
        markdown_cell("## 3. Audit rapide: nulls, doublons, anomalies"),
        code_cell("""audit = []
for name, df in raw.items():
    for col, count in df.isna().sum().items():
        if count:
            audit.append((name, col, int(count), round(count / len(df), 4)))
pd.DataFrame(audit, columns=["table", "column", "nulls", "null_rate"]).sort_values(
    ["null_rate", "nulls"], ascending=False
).head(25)
"""),
        code_cell("""checks = {
    "wine_export vintage_id duplicates": raw["wine_export"].duplicated("vintage_id").sum(),
    "wine_export exact duplicates": raw["wine_export"].duplicated().sum(),
    "vintages id duplicates": raw["vintages"].duplicated("id").sum(),
    "regions missing id": raw["regions"]["region_id"].isna().sum(),
}
checks
"""),
        markdown_cell("## 4. Nettoyage reproductible\n\nLe script du carnet applique les corrections et reconstruit la base SQLite."),
        code_cell("""import runpy
runpy.run_path(str(OUT / "scripts" / "build_carnet.py"), run_name="__main__")
"""),
        markdown_cell("## 5. Verification SQLite"),
        code_cell("""conn = sqlite3.connect(DB_PATH)
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
    conn,
)
tables
"""),
        code_cell("""row_counts = []
for table in tables["name"]:
    row_counts.append((table, pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {table}", conn)["n"].iat[0]))
pd.DataFrame(row_counts, columns=["table", "rows"]).sort_values("table")
"""),
        code_cell("""conn.execute("PRAGMA foreign_keys = ON")
conn.execute("PRAGMA foreign_key_check").fetchall()
"""),
        markdown_cell("## 6. Requetes d'exercice"),
        code_cell("""pd.read_sql_query(
    '''
    SELECT w.country, ROUND(AVG(p.price), 2) AS avg_price, COUNT(*) AS offers
    FROM price_offers p
    JOIN vintages v ON v.id = p.vintage_id
    JOIN wines w ON w.wine_id = v.wine_id
    GROUP BY w.country
    HAVING offers >= 10
    ORDER BY avg_price DESC
    ''',
    conn,
)
"""),
        code_cell("""pd.read_sql_query(
    '''
    SELECT w.wine_name, COUNT(DISTINCT f.id) AS food_matches
    FROM wines w
    JOIN wine_food_pairings wf ON wf.wine_id = w.wine_id
    JOIN foods f ON f.id = wf.food_id
    GROUP BY w.wine_id, w.wine_name
    ORDER BY food_matches DESC, w.wine_name
    LIMIT 10
    ''',
    conn,
)
"""),
        markdown_cell("## 7. Hypotheses nulles"),
        code_cell("""price_rating = pd.read_sql_query(
    '''
    SELECT p.price, v.ratings_average, v.ratings_count
    FROM price_offers p
    JOIN vintages v ON v.id = p.vintage_id
    WHERE p.price IS NOT NULL
      AND v.ratings_average > 0
      AND v.ratings_count >= 10
    ''',
    conn,
)
price_rating[["price", "ratings_average"]].corr(method="spearman")
"""),
        code_cell("""# H0: prix et note moyenne ne sont pas associes.
rng = np.random.default_rng(42)
observed = price_rating["price"].corr(price_rating["ratings_average"], method="spearman")
permuted = []
for _ in range(1000):
    shuffled = rng.permutation(price_rating["ratings_average"].to_numpy())
    permuted.append(pd.Series(price_rating["price"]).corr(pd.Series(shuffled), method="spearman"))
p_value = (np.abs(permuted) >= abs(observed)).mean()
observed, p_value
"""),
        code_cell("""# H0: mono-cepage et multi-cepages ont le meme prix median.
grape_price = pd.read_sql_query(
    '''
    WITH grape_count AS (
      SELECT wine_id, COUNT(*) AS nb_grapes
      FROM wine_grapes
      GROUP BY wine_id
    )
    SELECT CASE WHEN gc.nb_grapes = 1 THEN 'mono' ELSE 'multi' END AS group_type,
           v.median_price
    FROM grape_count gc
    JOIN vintages v ON v.wine_id = gc.wine_id
    WHERE v.median_price IS NOT NULL
    ''',
    conn,
)
grape_price.groupby("group_type")["median_price"].describe()
"""),
        markdown_cell("## 8. Fermeture"),
        code_cell("conn.close()\n"),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_documents(raw: dict[str, pd.DataFrame], clean: dict[str, pd.DataFrame]) -> None:
    (OUT / "README.md").write_text(readme_markdown(), encoding="utf-8")
    (OUT / "01_audit_nettoyage.md").write_text(audit_markdown(raw, clean), encoding="utf-8")
    (OUT / "02_mcd_mld_mpd.md").write_text(model_markdown(), encoding="utf-8")
    (OUT / "03_integration_sqlite.md").write_text(integration_markdown(), encoding="utf-8")
    (OUT / "04_hypotheses.md").write_text(hypotheses_markdown(raw), encoding="utf-8")
    (OUT / "vivino_sqlite_carnet.ipynb").write_text(
        json.dumps(notebook(), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "scripts").mkdir(exist_ok=True)
    raw = load_csvs()
    clean = coerce_for_sqlite(clean_tables(raw))
    write_documents(raw, clean)
    build_database(clean)
    print(f"Base generee: {DB_PATH}")
    print(f"Schema genere: {SCHEMA_PATH}")
    print(f"Notebook genere: {OUT / 'vivino_sqlite_carnet.ipynb'}")


if __name__ == "__main__":
    main()
