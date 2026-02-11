# backend/app/api/exports/__init__.py
"""
Export modules for customer-specific Excel templates.

Usage:
- customer_export_template_registry: Registry of all customer templates + API
- meiko_customer_export_template: MEIKO-specific export (3 sheets)

Add new customer templates:
1. Create {customer}_customer_export_template.py
2. Register in customer_export_template_registry.CUSTOMER_TEMPLATES
"""

from . import customer_export_template_registry
from . import meiko_customer_export_template
