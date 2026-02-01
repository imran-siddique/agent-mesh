"""
OpenTelemetry Tracing Integration.

Provides distributed tracing for AgentMesh operations.
"""

from typing import Optional, Any
from functools import wraps
import os


def setup_tracing(
    service_name: str = "agentmesh",
    endpoint: Optional[str] = None,
    insecure: bool = False,
) -> None:
    """
    Setup OpenTelemetry tracing.
    
    Args:
        service_name: Service name for traces
        endpoint: OTLP endpoint (default: from OTEL_EXPORTER_OTLP_ENDPOINT env)
        insecure: Whether to use insecure connection (default: False, use TLS)
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        # OpenTelemetry not installed, skip setup
        return
    
    # Get endpoint from env or parameter
    endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        # No endpoint configured, skip
        return
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "agentmesh",
        "deployment.environment": os.getenv("AGENTMESH_ENV", "development"),
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Create OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=insecure)
    
    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "agentmesh"):
    """Get tracer instance."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None


def trace_operation(
    operation_name: str,
    agent_did: Optional[str] = None,
    trust_score: Optional[int] = None,
    policy_result: Optional[str] = None,
):
    """
    Decorator to trace an operation.
    
    Args:
        operation_name: Name of the operation
        agent_did: Optional agent DID
        trust_score: Optional trust score
        policy_result: Optional policy result (ALLOW/DENY)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer is None:
                # Tracing not available
                return await func(*args, **kwargs)
            
            with tracer.start_as_current_span(operation_name) as span:
                # Set attributes
                if agent_did:
                    span.set_attribute("agent.did", agent_did)
                if trust_score is not None:
                    span.set_attribute("agent.trust_score", trust_score)
                if policy_result:
                    span.set_attribute("policy.result", policy_result)
                
                # Set standard attributes
                span.set_attribute("operation.name", operation_name)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("operation.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)
            
            with tracer.start_as_current_span(operation_name) as span:
                if agent_did:
                    span.set_attribute("agent.did", agent_did)
                if trust_score is not None:
                    span.set_attribute("agent.trust_score", trust_score)
                if policy_result:
                    span.set_attribute("policy.result", policy_result)
                
                span.set_attribute("operation.name", operation_name)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("operation.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class TraceContext:
    """Context manager for manual tracing."""
    
    def __init__(
        self,
        operation_name: str,
        agent_did: Optional[str] = None,
        **attributes: Any,
    ):
        self.operation_name = operation_name
        self.agent_did = agent_did
        self.attributes = attributes
        self.span = None
    
    def __enter__(self):
        tracer = get_tracer()
        if tracer is None:
            return self
        
        self.span = tracer.start_span(self.operation_name)
        self.span.__enter__()
        
        # Set attributes
        if self.agent_did:
            self.span.set_attribute("agent.did", self.agent_did)
        
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_attribute("operation.status", "error")
                self.span.set_attribute("error.type", exc_type.__name__)
                self.span.set_attribute("error.message", str(exc_val))
                self.span.record_exception(exc_val)
            else:
                self.span.set_attribute("operation.status", "success")
            
            self.span.__exit__(exc_type, exc_val, exc_tb)
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span."""
        if self.span:
            self.span.set_attribute(key, value)
    
    def add_event(self, name: str, attributes: Optional[dict] = None):
        """Add event to current span."""
        if self.span:
            self.span.add_event(name, attributes or {})
