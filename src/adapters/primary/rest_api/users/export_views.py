import io
from typing import List, Dict

from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from openpyxl import Workbook

from src.adapters.secondary.database.models import User, Student
from src.infrastructure.security.permissions import IsAdminOnly


PRACTICANTE_HEADERS: List[str] = ['codigo', 'nombre_completo', 'apellido_completo', 'email', 'role', 'estado']
OTHER_HEADERS: List[str] = ['nombre_completo', 'apellido_completo', 'email', 'role', 'estado']


def _parse_bool(value: str | None):
    if value is None:
        return None
    v = value.strip().lower()
    if v in ('1', 'true', 'yes', 'y', 't'):
        return True
    if v in ('0', 'false', 'no', 'n', 'f'):
        return False
    return None


def _apply_filters(request, qs):
    role = request.GET.get('role')
    is_active = _parse_bool(request.GET.get('is_active'))
    email = request.GET.get('email')
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    dj_from = request.GET.get('date_joined_from')
    dj_to = request.GET.get('date_joined_to')

    if role:
        qs = qs.filter(role=role)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if email:
        qs = qs.filter(email__icontains=email)
    if first_name:
        qs = qs.filter(first_name__icontains=first_name)
    if last_name:
        qs = qs.filter(last_name__icontains=last_name)
    if dj_from:
        d = parse_date(dj_from)
        if d:
            qs = qs.filter(date_joined__date__gte=d)
    if dj_to:
        d = parse_date(dj_to)
        if d:
            qs = qs.filter(date_joined__date__lte=d)

    return qs.order_by('date_joined')


class ExportUsersXLSXView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOnly]

    @extend_schema(
        operation_id='users_export_xlsx',
        tags=['Users Export'],
        summary='Exportar usuarios a Excel',
        parameters=[
            OpenApiParameter(name='role', location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(name='is_active', location=OpenApiParameter.QUERY, required=False, type=bool),
            OpenApiParameter(name='email', location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(name='first_name', location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(name='last_name', location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(name='date_joined_from', location=OpenApiParameter.QUERY, required=False, type=str, description='YYYY-MM-DD'),
            OpenApiParameter(name='date_joined_to', location=OpenApiParameter.QUERY, required=False, type=str, description='YYYY-MM-DD'),
        ],
        responses={200: OpenApiResponse(description='XLSX export')},
    )
    def get(self, request):
        qs = _apply_filters(request, User.objects.all())
        # Agrupar por rol
        by_role: Dict[str, List[User]] = {}
        for u in qs:
            by_role.setdefault(u.role, []).append(u)

        wb = Workbook()
        # Limpiar hoja inicial por defecto si no la usamos
        default_ws = wb.active
        default_ws.title = 'Resumen'
        default_ws.append(['role', 'count'])
        for role, items in by_role.items():
            default_ws.append([role, len(items)])

        for role, items in by_role.items():
            ws = wb.create_sheet(title=role)
            if role == 'PRACTICANTE':
                ws.append(PRACTICANTE_HEADERS)
                # Cargar students en bloque
                user_ids = [u.id for u in items]
                students = {s.user_id: s for s in Student.objects.filter(user_id__in=user_ids)}
                for u in items:
                    s = students.get(u.id)
                    codigo = s.codigo_estudiante if s else ''
                    nombre = u.first_name
                    apellidos = u.last_name
                    ws.append([
                        codigo, nombre, apellidos, u.email, u.role, ('ACTIVO' if u.is_active else 'INACTIVO')
                    ])
            else:
                ws.append(OTHER_HEADERS)
                for u in items:
                    ws.append([
                        u.first_name, u.last_name, u.email, u.role, ('ACTIVO' if u.is_active else 'INACTIVO')
                    ])

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)
        resp = HttpResponse(
            bio.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = 'attachment; filename="users_export.xlsx"'
        return resp
