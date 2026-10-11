# Carnet de bord - Vivino SQLite

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
