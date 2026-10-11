# Vivino SQLite

Projet pedagogique de nettoyage des exports Vivino, modelisation MCD / MLD / MPD
et integration dans SQLite.

Le [carnet de bord](carnet%20de%20bord/README.md) contient le notebook corrige,
les audits, le schema SQL et la base generee. Les CSV sources sont dans `vivino/`.

## Reconstruction

```powershell
python -m pip install -r "carnet de bord/requirements.txt"
python "carnet de bord/scripts/build_carnet.py"
```

Les notebooks MySQL d'origine restent locaux et sont exclus du depot.
