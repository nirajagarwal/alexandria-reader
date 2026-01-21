import json
import logging
from pathlib import Path
from datetime import datetime

from .config import OUTPUT_DIR
from .models import PipelineContext, Book
from .stages.planner import Planner
from .stages.drafter import Drafter
from .stages.enricher import Enricher
from .stages.publisher import Publisher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, collection_id: str, resume_from: int = 0, skip_existing: bool = False, workers: int = 5):
        self.context = PipelineContext(
            collection_id=collection_id,
            resume_from=resume_from,
            skip_existing=skip_existing,
            workers=workers
        )
        self.stages = [
            Planner(self.context),
            Drafter(self.context),
            Enricher(self.context),
            Publisher(self.context)
        ]

    def run(self):
        logger.info(f"Starting pipeline for collection: {self.context.collection_id}")
        
        # Initial Data is just the collection ID
        data = self.context.collection_id
        
        try:
            for stage in self.stages:
                stage_name = stage.__class__.__name__
                logger.info(f"Executing stage: {stage_name}")
                
                # Execute stage
                data = stage.execute(data)
                
                # Checkpointing could go here (save intermediate 'data' object)
                
            logger.info("Pipeline completed successfully.")
            self._print_stats()
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise e

    def _print_stats(self):
        stats = self.context.stats
        print("\nPipeline Statistics:")
        print(f"  Entries Processed: {stats['processed']}")
        print(f"  Failed:            {stats['failed']}")
        print(f"  Input Tokens:      {stats['tokens_in']}")
        print(f"  Output Tokens:     {stats['tokens_out']}")

    def save_state(self):
        # TODO: Implement robust state saving if needed beyond file outputs
        pass
