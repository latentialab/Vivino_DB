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
