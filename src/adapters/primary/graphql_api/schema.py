"""
Schema principal de GraphQL para el sistema de gestión de prácticas profesionales.
"""

import graphene
import graphql_jwt

from .queries import Query
from .mutations import Mutation


class Schema(graphene.Schema):
    """Schema principal que combina queries y mutations."""
    
    query = Query
    mutation = Mutation


# Schema para usar en Django settings
schema = Schema
