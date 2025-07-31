"""
Value Objects para el dominio de gestión de prácticas profesionales.
Los Value Objects son objetos inmutables que representan conceptos del dominio.
"""

import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Email:
    """Value Object para email."""
    value: str

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Email inválido: {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Valida formato de email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def domain(self) -> str:
        """Retorna el dominio del email."""
        return self.value.split('@')[1]

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Documento:
    """Value Object para número de documento."""
    numero: str
    tipo: str  # DNI, CE, PASSPORT, etc.

    def __post_init__(self):
        if not self.numero or not self.numero.strip():
            raise ValueError("El número de documento no puede estar vacío")
        
        if self.tipo == "DNI" and not self._is_valid_dni(self.numero):
            raise ValueError(f"DNI inválido: {self.numero}")

    @staticmethod
    def _is_valid_dni(dni: str) -> bool:
        """Valida formato de DNI peruano."""
        return bool(re.match(r'^\d{8}$', dni))

    def __str__(self):
        return f"{self.tipo}: {self.numero}"


@dataclass(frozen=True)
class Telefono:
    """Value Object para número de teléfono."""
    numero: str
    codigo_pais: str = "+51"

    def __post_init__(self):
        if not self._is_valid_phone(self.numero):
            raise ValueError(f"Número de teléfono inválido: {self.numero}")

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Valida formato de teléfono."""
        # Permite números de 9 dígitos (móvil) o 7 dígitos (fijo)
        pattern = r'^[0-9]{7,9}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

    def formato_completo(self) -> str:
        """Retorna el teléfono con código de país."""
        return f"{self.codigo_pais} {self.numero}"

    def __str__(self):
        return self.numero


@dataclass(frozen=True)
class Direccion:
    """Value Object para dirección."""
    calle: str
    numero: Optional[str] = None
    distrito: Optional[str] = None
    provincia: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None

    def __post_init__(self):
        if not self.calle or not self.calle.strip():
            raise ValueError("La calle no puede estar vacía")

    def direccion_completa(self) -> str:
        """Retorna la dirección completa formateada."""
        partes = [self.calle]
        
        if self.numero:
            partes[0] = f"{self.calle} {self.numero}"
        
        if self.distrito:
            partes.append(self.distrito)
        
        if self.provincia:
            partes.append(self.provincia)
        
        if self.departamento:
            partes.append(self.departamento)
        
        return ", ".join(partes)

    def __str__(self):
        return self.direccion_completa()


@dataclass(frozen=True)
class Periodo:
    """Value Object para periodo de tiempo."""
    fecha_inicio: datetime
    fecha_fin: datetime

    def __post_init__(self):
        if self.fecha_inicio >= self.fecha_fin:
            raise ValueError("La fecha de inicio debe ser menor a la fecha de fin")

    def duracion_dias(self) -> int:
        """Retorna la duración en días."""
        return (self.fecha_fin - self.fecha_inicio).days

    def duracion_semanas(self) -> int:
        """Retorna la duración en semanas."""
        return self.duracion_dias() // 7

    def esta_activo(self, fecha: Optional[datetime] = None) -> bool:
        """Verifica si el periodo está activo en la fecha dada."""
        if fecha is None:
            fecha = datetime.now()
        return self.fecha_inicio <= fecha <= self.fecha_fin

    def se_superpone_con(self, otro_periodo: 'Periodo') -> bool:
        """Verifica si este periodo se superpone con otro."""
        return (self.fecha_inicio <= otro_periodo.fecha_fin and 
                self.fecha_fin >= otro_periodo.fecha_inicio)

    def __str__(self):
        return f"{self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"


@dataclass(frozen=True)
class Calificacion:
    """Value Object para calificaciones."""
    valor: float
    escala_maxima: float = 20.0  # Sistema vigesimal peruano

    def __post_init__(self):
        if not 0 <= self.valor <= self.escala_maxima:
            raise ValueError(f"La calificación debe estar entre 0 y {self.escala_maxima}")

    def es_aprobatoria(self, nota_minima: float = 11.0) -> bool:
        """Verifica si la calificación es aprobatoria."""
        return self.valor >= nota_minima

    def calificacion_literal(self) -> str:
        """Convierte la calificación numérica a literal."""
        if self.valor >= 18:
            return "Excelente"
        elif self.valor >= 15:
            return "Bueno"
        elif self.valor >= 11:
            return "Regular"
        else:
            return "Deficiente"

    def porcentaje(self) -> float:
        """Convierte la calificación a porcentaje."""
        return (self.valor / self.escala_maxima) * 100

    def __str__(self):
        return f"{self.valor}/{self.escala_maxima}"


@dataclass(frozen=True)
class CodigoEstudiante:
    """Value Object para código de estudiante."""
    codigo: str

    def __post_init__(self):
        if not self._is_valid_codigo(self.codigo):
            raise ValueError(f"Código de estudiante inválido: {self.codigo}")

    @staticmethod
    def _is_valid_codigo(codigo: str) -> bool:
        """Valida formato de código de estudiante (ej: 2021001234)."""
        # Formato: YYYY + 6 dígitos
        pattern = r'^20\d{8}$'
        return bool(re.match(pattern, codigo))

    def año_ingreso(self) -> int:
        """Extrae el año de ingreso del código."""
        return int(self.codigo[:4])

    def numero_secuencial(self) -> str:
        """Extrae el número secuencial del código."""
        return self.codigo[4:]

    def __str__(self):
        return self.codigo


@dataclass(frozen=True)
class RUC:
    """Value Object para RUC de empresa."""
    numero: str

    def __post_init__(self):
        if not self._is_valid_ruc(self.numero):
            raise ValueError(f"RUC inválido: {self.numero}")

    @staticmethod
    def _is_valid_ruc(ruc: str) -> bool:
        """Valida formato de RUC peruano."""
        if not re.match(r'^\d{11}$', ruc):
            return False
        
        # Validación del dígito verificador
        suma = 0
        factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        
        for i in range(10):
            suma += int(ruc[i]) * factores[i]
        
        resto = suma % 11
        digito_verificador = 11 - resto if resto >= 2 else resto
        
        return digito_verificador == int(ruc[10])

    def tipo_contribuyente(self) -> str:
        """Determina el tipo de contribuyente según el RUC."""
        primer_digito = self.numero[0]
        segundo_digito = self.numero[1]
        
        if primer_digito == '1':
            return "Persona Natural"
        elif primer_digito == '2':
            if segundo_digito == '0':
                return "Empresa"
            else:
                return "Entidad del Estado"
        else:
            return "Otro"

    def __str__(self):
        return self.numero
