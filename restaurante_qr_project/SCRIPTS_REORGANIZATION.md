# Scripts Reorganization Plan

## Current State
Scripts in `restaurante_qr_project/scripts/` are standalone Python files that are NOT imported during Django runtime. They are dev/ops utilities.

## Recommended Reorganization

### Option A: Convert to Django Management Commands (RECOMMENDED)
**Benefits:** Native Django integration, consistent interface, automatic discovery

#### Dev Commands (DEBUG=True only):
- `scripts/dev/print_admin_models.py` → `app/core/management/commands/print_admin_models.py`
- `scripts/dev/verificar_adminux.py` → `app/adminux/management/commands/verificar_adminux.py`
- `scripts/crear_datos_iniciales.py` → `app/core/management/commands/seed_dev.py`

#### Ops Commands (production-safe):
- `scripts/actualizar_mesas.py` → `app/mesas/management/commands/actualizar_mesas.py`
- `scripts/regenerar_qr.py` → `app/mesas/management/commands/regenerar_qr_mesas.py`
  - Add `--host` and `--scheme` arguments
- `scripts/regenerar_qr_empleados.py` → `app/usuarios/management/commands/regenerar_qr_empleados.py`
  - Add `--host` and `--scheme` arguments
- `scripts/verificar_qr_empleados.py` → `app/usuarios/management/commands/verificar_qr_empleados.py`
  - Add `--host` argument

### Option B: Keep as Scripts but Organize
**Directory structure:**
```
scripts/
  ├── dev/          # Development-only scripts
  │   ├── print_admin_models.py
  │   └── verificar_adminux.py
  ├── ops/          # Operations/maintenance scripts
  │   ├── backup.sh  (keep - Postgres + media backup)
  │   ├── actualizar_mesas.py
  │   ├── regenerar_qr.py
  │   ├── regenerar_qr_empleados.py
  │   └── verificar_qr_empleados.py
  └── README.md     # Usage documentation
```

## Files to Delete
- `scripts/backup_sqlite.py` - SQLite backup not needed (using Postgres in production)

## Files to Keep
- `scripts/backup.sh` - Postgres + media backup (production-critical)

## Implementation Status
- [x] Code fixes applied (states, queries, tests)
- [ ] Scripts reorganized (deferred to avoid breaking existing workflows)
- [ ] Documentation created (this file)

## Migration Path
1. **Phase 1 (Current):** Document reorganization plan
2. **Phase 2 (Next Sprint):** Create management commands alongside existing scripts
3. **Phase 3 (After testing):** Deprecate old scripts, update docs/CI/CD
4. **Phase 4 (Cleanup):** Remove deprecated scripts

## Usage Examples

### Current (scripts/):
```bash
python scripts/regenerar_qr.py 10.165.187.107:8000
```

### Future (management commands):
```bash
python manage.py regenerar_qr_mesas --host 10.165.187.107:8000
# or
python manage.py regenerar_qr_mesas --host 10.165.187.107 --port 8000 --scheme https
```

## Notes
- Scripts are NOT part of runtime code, so NO immediate action needed
- Reorganization is **cosmetic improvement**, not a blocker
- Existing scripts continue to work as-is