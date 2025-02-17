async def _handle_scraping_failure(self, task_info: TaskInfo,
                                     error: Exception) -> bool:
        """
        Handle scraping failure with schema regeneration
        
        Args:
            task_info: Current task information
            error: The exception that occurred
            
        Returns:
            bool: True if retry should be attempted, False otherwise
            
        This method handles two main failure cases:
        1. Missing content (MissingContentError)
        2. Failed extraction (ExtractionError) when schema hasn't been regenerated yet
        """
        try:
            should_regenerate = (
                isinstance(error, MissingContentError) or
                (isinstance(error, ExtractionError) and not task_info.schema_regenerated)
            )
            
            if not should_regenerate:
                return False
            
            # Log appropriate message
            message = (
                "Content missing"
                if isinstance(error, MissingContentError)
                else "Extraction failed"
            )
            logger.warning(
                f"{message} for {task_info.url}, regenerating schema..."
            )
            
            try:
                # Regenerate schema
                config = await self.scraper._generate_config(task_info.url)
                await self.scraper.config_service.save_config(
                    task_info.url,
                    config
                )
                
                # Update task info
                task_info.schema_regenerated = True
                await self.storage.save_task(task_info.task_id, task_info)
                
                logger.info(f"Successfully regenerated schema for {task_info.url}")
                return True
                
            except Exception as schema_error:
                logger.error(
                    f"Schema regeneration failed for {task_info.url}: {str(schema_error)}",
                    exc_info=True
                )
                # Update task with schema regeneration failure
                task_info.error = f"Schema regeneration failed: {str(schema_error)}"
                await self.storage.save_task(task_info.task_id, task_info)
                return False
            
        except Exception as e:
            logger.error(
                f"Unexpected error in failure handling for {task_info.url}: {str(e)}",
                exc_info=True
            )
            return False