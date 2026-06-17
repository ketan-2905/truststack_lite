"""Domain services / repositories.

All data access is tenant-scoped here so the no-cross-tenant-reads guarantee is
enforced in one place rather than scattered across routers.
"""
