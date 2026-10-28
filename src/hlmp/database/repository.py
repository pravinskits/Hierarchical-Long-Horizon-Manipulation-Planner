import time
from sqlalchemy.orm import Session
from src.hlmp.database.models import TaskRecord

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create_task(self, task_id: str, goal: str) -> TaskRecord:
        now = time.time()
        record = TaskRecord(
            id=task_id,
            goal=goal,
            status="NOT_STARTED",
            progress_percentage=0.0,
            created_at=now,
            updated_at=now
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
        
    def get_task(self, task_id: str) -> TaskRecord:
        return self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        
    def update_task_status(self, task_id: str, status: str, progress: float = None):
        record = self.get_task(task_id)
        if record:
            record.status = status
            if progress is not None:
                record.progress_percentage = progress
            record.updated_at = time.time()
            self.db.commit()
            self.db.refresh(record)
        return record
        
    def add_failure(self, task_id: str, skill: str, subgoal: str, ftype: str, message: str):
        from src.hlmp.database.models import FailureRecord
        record = FailureRecord(
            task_id=task_id, timestamp=time.time(), skill_name=skill,
            subgoal_id=subgoal, failure_type=ftype, message=message
        )
        self.db.add(record)
        self.db.commit()
        
    def get_failures(self, task_id: str):
        from src.hlmp.database.models import FailureRecord
        return self.db.query(FailureRecord).filter(FailureRecord.task_id == task_id).all()
        
    def add_recovery(self, task_id: str, strategy: str, ftype: str, success: bool):
        from src.hlmp.database.models import RecoveryRecord
        record = RecoveryRecord(
            task_id=task_id, timestamp=time.time(), strategy=strategy,
            failure_type=ftype, success=success
        )
        self.db.add(record)
        self.db.commit()
        
    def get_recoveries(self, task_id: str):
        from src.hlmp.database.models import RecoveryRecord
        return self.db.query(RecoveryRecord).filter(RecoveryRecord.task_id == task_id).all()
