"""
Batch operations module for the Dataverse SDK.

This module provides efficient batch processing capabilities with auto-chunking,
parallel execution, and comprehensive error handling.
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import structlog

from ..client import AsyncDataverseClient
from ..exceptions import BatchOperationError, ValidationError
from ..hooks import HookContext, HookType
from ..models import BatchRequest, BatchResponse, BulkOperationResult
from ..utils import chunk_list


logger = structlog.get_logger(__name__)


class BatchProcessor:
    """
    Handles batch operations for the Dataverse SDK.
    
    Features:
    - Auto-chunking of large batches
    - Parallel execution of chunks
    - Comprehensive error handling
    - Progress tracking
    - Hook integration
    """
    
    def __init__(
        self,
        client: AsyncDataverseClient,
        default_batch_size: int = 100,
        max_batch_size: int = 1000,
        max_parallel_batches: int = 5,
    ) -> None:
        """
        Initialize batch processor.
        
        Args:
            client: Dataverse client instance
            default_batch_size: Default batch size for operations
            max_batch_size: Maximum allowed batch size
            max_parallel_batches: Maximum number of parallel batch executions
        """
        self.client = client
        self.default_batch_size = default_batch_size
        self.max_batch_size = max_batch_size
        self.max_parallel_batches = max_parallel_batches
        
        logger.debug(
            "Batch processor initialized",
            default_batch_size=default_batch_size,
            max_batch_size=max_batch_size,
            max_parallel_batches=max_parallel_batches,
        )
    
    def _create_batch_boundary(self) -> str:
        """Create a unique batch boundary identifier."""
        return f"batch_{uuid.uuid4().hex}"
    
    def _create_changeset_boundary(self) -> str:
        """Create a unique changeset boundary identifier."""
        return f"changeset_{uuid.uuid4().hex}"
    
    def _build_batch_payload(
        self,
        requests: List[Dict[str, Any]],
        batch_boundary: str,
        changeset_boundary: Optional[str] = None,
    ) -> str:
        """
        Build the batch request payload.
        
        Args:
            requests: List of HTTP requests
            batch_boundary: Batch boundary identifier
            changeset_boundary: Changeset boundary identifier for transactional operations
            
        Returns:
            Batch payload string
        """
        lines = [f"--{batch_boundary}"]
        
        if changeset_boundary:
            # Transactional changeset
            lines.extend([
                "Content-Type: multipart/mixed; boundary=" + changeset_boundary,
                "",
                f"--{changeset_boundary}",
            ])
        
        for i, request in enumerate(requests):
            if changeset_boundary and i > 0:
                lines.append(f"--{changeset_boundary}")
            elif not changeset_boundary and i > 0:
                lines.append(f"--{batch_boundary}")
            
            # Request headers
            lines.extend([
                "Content-Type: application/http",
                "Content-Transfer-Encoding: binary",
                "",
            ])
            
            # HTTP request line
            method = request["method"]
            url = request["url"]
            lines.append(f"{method} {url} HTTP/1.1")
            
            # Request headers
            headers = request.get("headers", {})
            for header_name, header_value in headers.items():
                lines.append(f"{header_name}: {header_value}")
            
            # Content-Type for requests with body
            if request.get("body") and "Content-Type" not in headers:
                lines.append("Content-Type: application/json")
            
            lines.append("")  # Empty line before body
            
            # Request body
            if request.get("body"):
                import json
                lines.append(json.dumps(request["body"]))
            
            lines.append("")  # Empty line after request
        
        if changeset_boundary:
            lines.extend([
                f"--{changeset_boundary}--",
                "",
                f"--{batch_boundary}--",
            ])
        else:
            lines.append(f"--{batch_boundary}--")
        
        return "\r\n".join(lines)
    
    def _parse_batch_response(self, response_content: str) -> BatchResponse:
        """
        Parse batch response content.
        
        Args:
            response_content: Raw batch response content
            
        Returns:
            Parsed batch response
        """
        responses = []
        errors = []
        
        # Simple parsing - in production, you'd want more robust parsing
        parts = response_content.split("--")
        
        for part in parts:
            if "HTTP/1.1" in part:
                lines = part.strip().split("\n")
                status_line = None
                headers = {}
                body = ""
                
                # Find status line
                for line in lines:
                    if line.startswith("HTTP/1.1"):
                        status_line = line
                        break
                
                if status_line:
                    status_code = int(status_line.split()[1])
                    
                    # Parse headers and body (simplified)
                    in_body = False
                    for line in lines:
                        if in_body:
                            body += line + "\n"
                        elif line.strip() == "":
                            in_body = True
                        elif ":" in line and not in_body:
                            key, value = line.split(":", 1)
                            headers[key.strip()] = value.strip()
                    
                    response_data = {
                        "status": status_code,
                        "headers": headers,
                        "body": body.strip(),
                    }
                    
                    # Try to parse JSON body
                    if body.strip():
                        try:
                            import json
                            response_data["json"] = json.loads(body.strip())
                        except json.JSONDecodeError:
                            pass
                    
                    if status_code >= 400:
                        errors.append(response_data)
                    else:
                        responses.append(response_data)
        
        return BatchResponse(responses=responses, errors=errors)
    
    async def execute_batch(
        self,
        requests: List[Dict[str, Any]],
        transactional: bool = False,
    ) -> BatchResponse:
        """
        Execute a batch of requests.
        
        Args:
            requests: List of HTTP requests to execute
            transactional: Whether to execute as a transactional changeset
            
        Returns:
            Batch response with results and errors
            
        Raises:
            BatchOperationError: If batch execution fails
            ValidationError: If requests are invalid
        """
        if not requests:
            raise ValidationError("No requests provided for batch execution")
        
        if len(requests) > self.max_batch_size:
            raise ValidationError(f"Batch size {len(requests)} exceeds maximum {self.max_batch_size}")
        
        # Execute before_batch hooks
        context = HookContext(
            hook_type=HookType.BEFORE_BATCH,
            metadata={
                "request_count": len(requests),
                "transactional": transactional,
            },
        )
        
        if hasattr(self.client, "hook_manager"):
            context = await self.client.hook_manager.execute_hooks(HookType.BEFORE_BATCH, context)
        
        try:
            # Create boundaries
            batch_boundary = self._create_batch_boundary()
            changeset_boundary = self._create_changeset_boundary() if transactional else None
            
            # Build payload
            payload = self._build_batch_payload(requests, batch_boundary, changeset_boundary)
            
            # Set headers
            headers = {
                "Content-Type": f"multipart/mixed; boundary={batch_boundary}",
                "OData-Version": "4.0",
                "OData-MaxVersion": "4.0",
            }
            
            # Execute batch request
            response = await self.client._execute_request(
                method="POST",
                url=urljoin(self.client.api_base_url, "$batch"),
                headers=headers,
                content=payload.encode("utf-8"),
            )
            
            # Parse response
            batch_response = self._parse_batch_response(response.text)
            
            # Execute after_batch hooks
            after_context = HookContext(
                hook_type=HookType.AFTER_BATCH,
                metadata={
                    "request_count": len(requests),
                    "success_count": batch_response.success_count,
                    "error_count": batch_response.error_count,
                    "transactional": transactional,
                },
            )
            
            if hasattr(self.client, "hook_manager"):
                await self.client.hook_manager.execute_hooks(HookType.AFTER_BATCH, after_context)
            
            logger.info(
                "Batch executed",
                request_count=len(requests),
                success_count=batch_response.success_count,
                error_count=batch_response.error_count,
                transactional=transactional,
            )
            
            return batch_response
            
        except Exception as e:
            logger.error("Batch execution failed", error=str(e), request_count=len(requests))
            raise BatchOperationError(f"Batch execution failed: {str(e)}") from e
    
    async def execute_bulk_operation(
        self,
        operations: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = True,
        transactional: bool = False,
    ) -> BulkOperationResult:
        """
        Execute bulk operations with auto-chunking.
        
        Args:
            operations: List of operations to execute
            batch_size: Size of each batch (uses default if not specified)
            parallel: Whether to execute batches in parallel
            transactional: Whether each batch should be transactional
            
        Returns:
            Bulk operation result with statistics
        """
        if not operations:
            return BulkOperationResult()
        
        batch_size = batch_size or self.default_batch_size
        batch_size = min(batch_size, self.max_batch_size)
        
        # Split operations into chunks
        chunks = chunk_list(operations, batch_size)
        
        logger.info(
            "Starting bulk operation",
            total_operations=len(operations),
            batch_count=len(chunks),
            batch_size=batch_size,
            parallel=parallel,
            transactional=transactional,
        )
        
        result = BulkOperationResult(total_processed=len(operations))
        
        if parallel and len(chunks) > 1:
            # Execute batches in parallel
            semaphore = asyncio.Semaphore(self.max_parallel_batches)
            
            async def execute_chunk(chunk: List[Dict[str, Any]]) -> BatchResponse:
                async with semaphore:
                    return await self.execute_batch(chunk, transactional)
            
            # Execute all chunks
            tasks = [execute_chunk(chunk) for chunk in chunks]
            batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, response in enumerate(batch_responses):
                if isinstance(response, Exception):
                    # Batch failed entirely
                    chunk_size = len(chunks[i])
                    result.failed += chunk_size
                    result.errors.append({
                        "batch_index": i,
                        "error": str(response),
                        "operations_count": chunk_size,
                    })
                else:
                    # Process batch response
                    result.successful += response.success_count
                    result.failed += response.error_count
                    
                    # Add individual errors
                    for error in response.errors:
                        result.errors.append({
                            "batch_index": i,
                            "error": error,
                        })
        
        else:
            # Execute batches sequentially
            for i, chunk in enumerate(chunks):
                try:
                    response = await self.execute_batch(chunk, transactional)
                    result.successful += response.success_count
                    result.failed += response.error_count
                    
                    # Add individual errors
                    for error in response.errors:
                        result.errors.append({
                            "batch_index": i,
                            "error": error,
                        })
                
                except Exception as e:
                    # Batch failed entirely
                    chunk_size = len(chunk)
                    result.failed += chunk_size
                    result.errors.append({
                        "batch_index": i,
                        "error": str(e),
                        "operations_count": chunk_size,
                    })
        
        logger.info(
            "Bulk operation completed",
            total_processed=result.total_processed,
            successful=result.successful,
            failed=result.failed,
            success_rate=result.success_rate,
        )
        
        return result
    
    async def bulk_create(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk create entities.
        
        Args:
            entity_type: Entity logical name
            entities: List of entity data
            batch_size: Size of each batch
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        operations = []
        
        for entity_data in entities:
            operations.append({
                "method": "POST",
                "url": f"{entity_type}",
                "body": entity_data,
            })
        
        return await self.execute_bulk_operation(
            operations,
            batch_size=batch_size,
            parallel=parallel,
            transactional=False,
        )
    
    async def bulk_update(
        self,
        entity_type: str,
        updates: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk update entities.
        
        Args:
            entity_type: Entity logical name
            updates: List of updates (must include entity ID)
            batch_size: Size of each batch
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        operations = []
        
        for update_data in updates:
            entity_id = update_data.pop("id", None)
            if not entity_id:
                raise ValidationError("Entity ID is required for bulk update")
            
            operations.append({
                "method": "PATCH",
                "url": f"{entity_type}({entity_id})",
                "body": update_data,
            })
        
        return await self.execute_bulk_operation(
            operations,
            batch_size=batch_size,
            parallel=parallel,
            transactional=False,
        )
    
    async def bulk_delete(
        self,
        entity_type: str,
        entity_ids: List[str],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk delete entities.
        
        Args:
            entity_type: Entity logical name
            entity_ids: List of entity IDs to delete
            batch_size: Size of each batch
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        operations = []
        
        for entity_id in entity_ids:
            operations.append({
                "method": "DELETE",
                "url": f"{entity_type}({entity_id})",
            })
        
        return await self.execute_bulk_operation(
            operations,
            batch_size=batch_size,
            parallel=parallel,
            transactional=False,
        )


# Convenience exports
__all__ = [
    "BatchProcessor",
]

