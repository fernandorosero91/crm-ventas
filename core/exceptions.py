"""
Custom exception classes for CRM business logic errors.
Provides structured error handling across the application.
"""


class CRMBaseException(Exception):
    """
    Base exception for all CRM business logic errors.
    All custom exceptions should inherit from this class.
    """
    def __init__(self, message: str, code: str = None):
        """
        Initialize CRM base exception.
        
        Args:
            message: Human-readable error message
            code: Optional error code for programmatic handling
        """
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class StageTransitionError(CRMBaseException):
    """
    Raised when an invalid pipeline stage transition is attempted.
    
    Examples:
    - Vendedor attempting to move opportunity backward
    - Moving to close stage without required fields
    - Invalid stage sequence
    """
    def __init__(self, message: str = "Transición de etapa inválida", code: str = "INVALID_STAGE_TRANSITION"):
        super().__init__(message, code)


class InsufficientPermissionError(CRMBaseException):
    """
    Raised when a user lacks permission for an operation.
    
    Examples:
    - Vendedor accessing another vendedor's clients
    - Non-admin attempting to create users
    - Role-based access violations
    """
    def __init__(self, message: str = "Permisos insuficientes para esta operación", code: str = "INSUFFICIENT_PERMISSION"):
        super().__init__(message, code)


class DataIntegrityError(CRMBaseException):
    """
    Raised when an operation would violate data integrity rules.
    
    Examples:
    - Duplicate email addresses
    - Invalid foreign key references
    - Constraint violations
    """
    def __init__(self, message: str = "Error de integridad de datos", code: str = "DATA_INTEGRITY_ERROR"):
        super().__init__(message, code)


class ExportLimitExceededError(CRMBaseException):
    """
    Raised when export exceeds the maximum allowed record limit.
    
    The system limits exports to prevent performance issues and
    excessive resource consumption.
    """
    def __init__(self, message: str = "Límite de exportación excedido (máximo 10,000 registros)", code: str = "EXPORT_LIMIT_EXCEEDED"):
        super().__init__(message, code)


class ValidationError(CRMBaseException):
    """
    Raised when input validation fails.
    
    Examples:
    - Invalid email format
    - Phone number format errors
    - Field length violations
    """
    def __init__(self, message: str = "Error de validación", code: str = "VALIDATION_ERROR"):
        super().__init__(message, code)


class ClientInactiveError(CRMBaseException):
    """
    Raised when attempting operations on inactive clients.
    
    Examples:
    - Creating opportunities for inactive clients
    - Assigning inactive clients to vendedores
    """
    def __init__(self, message: str = "El cliente está inactivo", code: str = "CLIENT_INACTIVE"):
        super().__init__(message, code)


class OpportunityClosedError(CRMBaseException):
    """
    Raised when attempting to modify closed opportunities.
    
    Closed opportunities (Cierre Ganado/Perdido) have restrictions
    on modifications to preserve data integrity.
    """
    def __init__(self, message: str = "No se puede modificar una oportunidad cerrada", code: str = "OPPORTUNITY_CLOSED"):
        super().__init__(message, code)
