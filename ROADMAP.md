# ROADMAP — Detector de Duplicados

## Estado actual: v1.1.0 (Estable)

| Métrica | Valor |
|---------|-------|
| Tests | 450 passed, 0 failures |
| Ruff | ✅ limpio |
| Build | ✅ PyInstaller --onedir (4.6 MB) |
| CI | ✅ GitHub Actions |
| Release | ✅ v1.0.0 y v1.1.0 en GitHub |

## Principios

1. Terminal ligera con Rich — nunca GUI
2. Nunca sobreingeniería
3. No servidor, no auth, no complicaciones
4. Si se puede simplificar, simplificar
5. Pruebas como garantía

## Arquitectura

```
Detector de duplicados_/
├── src/detector_duplicados/
│   ├── cli.py           # CLI Rich Prompt
│   ├── main.py          # Entry point
│   ├── ui.py            # UI Rich
│   ├── duper.py         # Detección (tamaño + hash)
│   ├── scanner.py       # Escaneo filesystem
│   ├── db.py            # SQLite
│   ├── config.py        # Configuración + perfiles
│   ├── policies.py      # 6 políticas de conservación
│   ├── exporter.py      # Exportación HTML/CSV/JSON/TXT
│   ├── html_report.py   # Reporte HTML autocontenido
│   ├── cleaner.py       # Gestión de duplicados
│   ├── watchdog.py      # Escaneo incremental
│   └── theme.py         # Tema Rich
├── tests/               # 450 tests
├── .github/workflows/
│   └── build.yml        # CI
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

## Release History

- **v1.0.0** — Release inicial, fases 1-7 completas
- **v1.1.0** — Bug fixes: db.py (mkdir padre + DB corrupta), main.py (sospechosos), html_report.py (dual format), ui.py (dual format)

## Instalación

```bash
pip install -e .
detector --help
```

## Build

```bash
pyinstaller --onedir --name DetectorDeDuplicados src/detector_duplicados/cli.py
```

*Última actualización: 2026-06-27*
