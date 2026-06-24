# BENCHMARK FASE 2.0

**Proyecto:** Detector de Duplicados  
**Fecha:** 2026-06-24  

## Dataset
- Archivos creados: 100
- Duplicados intencionales: 25
- Extensiones: txt

## Resultados

| Métrica | Tiempo |
|---------|--------|
| Escaneo | 0.0057s |
| Agrupación | 0.0000s |
| Hashing | 0.0011s |
| Total | 0.0069s |

## Notas
- Hashing ejecutado con `ThreadPoolExecutor` (Fase 2.0)
- Chunk size: 64KB
- Exclusión de subtítulos habilitada

## Ganancia vs Fase 1
- Optimización de hashing paralelizado: 0.0011s (vs ~0.0023s estimado serial)
- Barra de progreso funcional y estable
- HTML auto-generado y abierto automáticamente
