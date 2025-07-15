"""
Hook system for the Dataverse SDK.

This module provides a flexible hook system that allows users to intercept
and modify requests/responses, add custom logging, telemetry, and other
extensibility features.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

import structlog


logger = structlog.get_logger(__name__)


class HookType(Enum):
    """Types of hooks supported by the SDK."""
    
    BEFORE_REQUEST = "before_request"
    AFTER_RESPONSE = "after_response"
    ON_ERROR = "on_error"
    BEFORE_BATCH = "before_batch"
    AFTER_BATCH = "after_batch"
    ON_RETRY = "on_retry"
    ON_RATE_LIMIT = "on_rate_limit"


class HookContext:
    """Context object passed to hook functions."""
    
    def __init__(
        self,
        hook_type: HookType,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.hook_type = hook_type
        self.request_data = request_data or {}
        self.response_data = response_data or {}
        self.error = error
        self.metadata = metadata or {}
        self.custom_data: Dict[str, Any] = {}
    
    def set_custom_data(self, key: str, value: Any) -> None:
        """Set custom data that can be accessed by other hooks."""
        self.custom_data[key] = value
    
    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """Get custom data set by other hooks."""
        return self.custom_data.get(key, default)


# Type alias for hook functions
HookFunction = Callable[[HookContext], Union[None, Dict[str, Any]]]
AsyncHookFunction = Callable[[HookContext], Union[None, Dict[str, Any]]]


class HookManager:
    """Manages registration and execution of hooks."""
    
    def __init__(self) -> None:
        self._hooks: Dict[HookType, List[Union[HookFunction, AsyncHookFunction]]] = {
            hook_type: [] for hook_type in HookType
        }
        self._lock = asyncio.Lock()
    
    def register_hook(
        self,
        hook_type: HookType,
        hook_func: Union[HookFunction, AsyncHookFunction],
        priority: int = 0,
    ) -> None:
        """
        Register a hook function.
        
        Args:
            hook_type: Type of hook to register
            hook_func: Hook function to register
            priority: Priority for hook execution (higher = earlier)
        """
        # Store hook with priority for sorting
        hook_entry = (priority, hook_func)
        self._hooks[hook_type].append(hook_entry)
        
        # Sort hooks by priority (descending)
        self._hooks[hook_type].sort(key=lambda x: x[0], reverse=True)
        
        logger.debug(
            "Hook registered",
            hook_type=hook_type.value,
            function=hook_func.__name__,
            priority=priority,
        )
    
    def unregister_hook(
        self,
        hook_type: HookType,
        hook_func: Union[HookFunction, AsyncHookFunction],
    ) -> bool:
        """
        Unregister a hook function.
        
        Args:
            hook_type: Type of hook to unregister
            hook_func: Hook function to unregister
            
        Returns:
            True if hook was found and removed, False otherwise
        """
        hooks = self._hooks[hook_type]
        for i, (priority, func) in enumerate(hooks):
            if func == hook_func:
                del hooks[i]
                logger.debug(
                    "Hook unregistered",
                    hook_type=hook_type.value,
                    function=hook_func.__name__,
                )
                return True
        return False
    
    async def execute_hooks(
        self,
        hook_type: HookType,
        context: HookContext,
    ) -> HookContext:
        """
        Execute all registered hooks of a specific type.
        
        Args:
            hook_type: Type of hooks to execute
            context: Hook context to pass to functions
            
        Returns:
            Modified context after all hooks have executed
        """
        hooks = self._hooks.get(hook_type, [])
        
        if not hooks:
            return context
        
        logger.debug(
            "Executing hooks",
            hook_type=hook_type.value,
            hook_count=len(hooks),
        )
        
        for priority, hook_func in hooks:
            try:
                if asyncio.iscoroutinefunction(hook_func):
                    result = await hook_func(context)
                else:
                    result = hook_func(context)
                
                # If hook returns data, merge it into context
                if isinstance(result, dict):
                    if hook_type == HookType.BEFORE_REQUEST:
                        context.request_data.update(result)
                    elif hook_type == HookType.AFTER_RESPONSE:
                        context.response_data.update(result)
                    else:
                        context.metadata.update(result)
                
            except Exception as e:
                logger.error(
                    "Hook execution failed",
                    hook_type=hook_type.value,
                    function=hook_func.__name__,
                    error=str(e),
                )
                # Continue executing other hooks even if one fails
                continue
        
        return context
    
    def clear_hooks(self, hook_type: Optional[HookType] = None) -> None:
        """
        Clear registered hooks.
        
        Args:
            hook_type: Specific hook type to clear, or None to clear all
        """
        if hook_type:
            self._hooks[hook_type].clear()
            logger.debug("Hooks cleared", hook_type=hook_type.value)
        else:
            for hooks in self._hooks.values():
                hooks.clear()
            logger.debug("All hooks cleared")
    
    def get_hook_count(self, hook_type: Optional[HookType] = None) -> int:
        """
        Get the number of registered hooks.
        
        Args:
            hook_type: Specific hook type to count, or None for total
            
        Returns:
            Number of registered hooks
        """
        if hook_type:
            return len(self._hooks[hook_type])
        else:
            return sum(len(hooks) for hooks in self._hooks.values())


# Built-in hook functions for common use cases

def logging_hook(context: HookContext) -> None:
    """Built-in hook for logging requests and responses."""
    if context.hook_type == HookType.BEFORE_REQUEST:
        logger.info(
            "Making request",
            method=context.request_data.get("method"),
            url=context.request_data.get("url"),
            headers=context.request_data.get("headers", {}).keys(),
        )
    
    elif context.hook_type == HookType.AFTER_RESPONSE:
        logger.info(
            "Received response",
            status_code=context.response_data.get("status_code"),
            response_time=context.metadata.get("response_time"),
        )
    
    elif context.hook_type == HookType.ON_ERROR:
        logger.error(
            "Request failed",
            error=str(context.error),
            url=context.request_data.get("url"),
        )


def telemetry_hook(context: HookContext) -> None:
    """Built-in hook for telemetry collection."""
    # This would integrate with OpenTelemetry or similar
    if context.hook_type == HookType.BEFORE_REQUEST:
        # Start span
        context.set_custom_data("span_start_time", asyncio.get_event_loop().time())
    
    elif context.hook_type == HookType.AFTER_RESPONSE:
        # End span
        start_time = context.get_custom_data("span_start_time")
        if start_time:
            duration = asyncio.get_event_loop().time() - start_time
            context.metadata["response_time"] = duration


def retry_logging_hook(context: HookContext) -> None:
    """Built-in hook for logging retry attempts."""
    if context.hook_type == HookType.ON_RETRY:
        logger.warning(
            "Retrying request",
            attempt=context.metadata.get("attempt"),
            max_attempts=context.metadata.get("max_attempts"),
            error=str(context.error),
        )


def rate_limit_hook(context: HookContext) -> None:
    """Built-in hook for handling rate limits."""
    if context.hook_type == HookType.ON_RATE_LIMIT:
        retry_after = context.metadata.get("retry_after", 60)
        logger.warning(
            "Rate limit encountered",
            retry_after=retry_after,
            url=context.request_data.get("url"),
        )


# Decorator for easy hook registration
def hook(hook_type: HookType, priority: int = 0):
    """
    Decorator for registering hook functions.
    
    Args:
        hook_type: Type of hook to register
        priority: Priority for hook execution
    """
    def decorator(func: Union[HookFunction, AsyncHookFunction]):
        # Store hook metadata on function
        func._hook_type = hook_type
        func._hook_priority = priority
        return func
    
    return decorator


# Global hook manager instance
_global_hook_manager = HookManager()


def register_global_hook(
    hook_type: HookType,
    hook_func: Union[HookFunction, AsyncHookFunction],
    priority: int = 0,
) -> None:
    """Register a hook in the global hook manager."""
    _global_hook_manager.register_hook(hook_type, hook_func, priority)


def unregister_global_hook(
    hook_type: HookType,
    hook_func: Union[HookFunction, AsyncHookFunction],
) -> bool:
    """Unregister a hook from the global hook manager."""
    return _global_hook_manager.unregister_hook(hook_type, hook_func)


async def execute_global_hooks(
    hook_type: HookType,
    context: HookContext,
) -> HookContext:
    """Execute hooks from the global hook manager."""
    return await _global_hook_manager.execute_hooks(hook_type, context)


def get_global_hook_manager() -> HookManager:
    """Get the global hook manager instance."""
    return _global_hook_manager


# Convenience exports
__all__ = [
    "HookType",
    "HookContext",
    "HookManager",
    "HookFunction",
    "AsyncHookFunction",
    "logging_hook",
    "telemetry_hook",
    "retry_logging_hook",
    "rate_limit_hook",
    "hook",
    "register_global_hook",
    "unregister_global_hook",
    "execute_global_hooks",
    "get_global_hook_manager",
]

