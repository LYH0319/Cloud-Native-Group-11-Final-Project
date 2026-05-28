from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.database.models import User, UserRole, HttpMethod, JobStatus, ScheduleType, Job
from typing import Any
from datetime import datetime
from src.database import schemas

# ==========================================
#                  USER CRUD
# ==========================================

def create_user(db: Session, user_in: schemas.UserCreate) -> User:
    """
    Creates a new user in the database.

    Args:
        db (Session): The database session.
        employee_id (str): The unique employee ID of the user.
        username (str): The display name of the user.
        role (UserRole): The authorization role of the user (e.g., DEVELOPER, OPERATOR).

    Returns:
        User: The newly created user object.
    """
    new_user = User(
        employee_id=user_in.employee_id, 
        username=user_in.username, 
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_user_id(db:Session, user_id: str) -> User | None:
    """
    Retrieves a user by their unique user ID.

    Args:
        db (Session): The database session.
        user_id (int): The specific user_id ID to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.scalar(select(User).where(User.user_id == user_id))


def get_user_by_employee_id(db:Session, employee_id: str) -> User | None:
    """
    Retrieves a user by their unique employee ID.

    Args:
        db (Session): The database session.
        employee_id (str): The specific employee ID to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.scalar(select(User).where(User.employee_id == employee_id))

def get_users(db:Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Retrieves a list of all active users with pagination.

    Note:
        This query filters out inactive users (soft-deleted accounts).

    Args:
        db (Session): The database session.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[User]: A list of active user objects.
    """
    return list(db.scalars(select(User).where(User.is_active == True).offset(skip).limit(limit)).all())

def change_user_role(db: Session, user_id: int, new_role: UserRole) -> User | None:
    """
    Updates the authorization role of a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The internal primary key of the user to update.
        new_role (UserRole): The new role to assign to the user.

    Returns:
        User | None: The updated user object, or None if the user does not exist.
    """
    user = db.scalar(select(User).where(User.user_id == user_id))
    
    if not user:
        return None
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """
    Performs a soft delete on a user account.

    Note:
        This function does not permanently remove the record from the database.
        Instead, it sets the 'is_active' flag to False.

    Args:
        db (Session): The database session.
        user_id (int): The internal primary key of the user to delete.

    Returns:
        bool: True if the user was successfully soft-deleted, False if the user was not found.
    """
    user = db.scalar(select(User).where(User.user_id == user_id))
    
    if not user or user.is_active == False:
        return False
    
    user.is_active = False
    db.commit()
    return True

# ==========================================
#                  JOB CRUD
# ==========================================

def create_job(
    db: Session,
    owner_id: int, 
    job_in: schemas.JobCreate, 
    next_run_time: datetime | None = None
) -> Job:
    """
    Creates a new HTTP request job in the database.

    Args:
        db (Session): The database session.
        owner_id (int): The internal user ID of the job's owner.
        job_name (str): The display name of the job.
        method (HttpMethod): The HTTP method (GET, POST, etc.) to be executed.
        endpoint (str): The target URL for the job.
        schedule_type (ScheduleType): Whether the job is ONE_TIME or RECURRING.
        has_dependency (bool, optional): Indicates if this job waits for others. Defaults to False.
        headers (dict | None, optional): HTTP headers for the request. Defaults to None.
        body (dict | None, optional): JSON payload for the request. Defaults to None.
        cron_expression (str | None, optional): The CRON schedule string (required if RECURRING). Defaults to None.
        
    Note:
        The job 'status' is automatically set to ACTIVE by the database model.

    Returns:
        Job: The newly created job object.
    """
    
    new_job = Job(
        owner_id=owner_id,
        job_name=job_in.job_name,
        method=job_in.method,
        endpoint=job_in.endpoint,
        headers=job_in.headers,
        body=job_in.body,
        has_dependency=job_in.has_dependency,
        schedule_type=job_in.schedule_type,
        cron_expression=job_in.cron_expression,
        next_run_time=next_run_time
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

def get_job_by_id(db: Session, job_id: int) -> Job | None:
    """
    Retrieves a specific job by its internal ID.

    Args:
        db (Session): The database session.
        job_id (int): The primary key of the job.

    Returns:
        Job | None: The job object if found, otherwise None.
    """
    return db.scalar(select(Job).where(Job.job_id == job_id))
    
def get_jobs_by_owner_id(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Job]:
    """
    Retrieves a list of jobs owned by a specific user with pagination.

    Note:
        This function returns all jobs belonging to the user, regardless of their status 
        (including ACTIVE, DISABLED, and DELETED). The frontend can filter them if needed.

    Args:
        db (Session): The database session.
        owner_id (int): The internal user ID of the job's owner.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[Job]: A list of job objects owned by the specified user.
    """
    return list(db.scalars(select(Job).where(Job.owner_id == owner_id).offset(skip).limit(limit)).all())

def get_active_jobs(
		db: Session,
		schedule_type: ScheduleType | None = None,
		target_time: datetime | None = None,
		skip: int = 0,
		limit: int = 100,
		for_update: bool = False
    ) -> list[Job]:
    """
    Retrieves a batch of ACTIVE jobs that are ready to be executed.

    Args:
        db (Session): The database session.
        schedule_type (ScheduleType | None): Filter by ONE_TIME or RECURRING. Defaults to None.
        target_time (datetime | None): The evaluation time. If None, uses the current database time.
        skip (int): 
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
		for_update (bool): If True, locks the selected rows for execution (skip_locked=True).
                           Should ONLY be True when called by the background scheduler.
                           
    Returns:
        list[Job]: A list of job objects locked for execution.
    """
    
    check_time = target_time if target_time else func.now()
    
    conditions = [
		Job.status == JobStatus.ACTIVE,
		Job.next_run_time <= check_time,
	]
    if schedule_type:
        conditions.append(Job.schedule_type == schedule_type)
        
    stm = select(Job).where(*conditions).offset(skip).limit(limit)
    
    if for_update:
        stm = stm.with_for_update(skip_locked=True)
    
    return list(db.scalars(stm).all())

def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> list[Job]:
    """
    Retrieves a list of all jobs in the system with pagination.
    
    Note:
        This is typically used by System Administrators for dashboard monitoring.
    """
    return list(db.scalars(select(Job).offset(skip).limit(limit)).all())



"""

### 1. 核心實體：`User` 與 `Job`

這兩個是系統的主角，通常會需要比較完整的 CRUD，但也有例外：

* **Create (新增):** 兩者都需要。
* **Read (讀取):** 兩者都需要（例如：用 `employee_id` 找 User、列出某個 User 的所有 Jobs）。
* **Update (更新):** `Job` 很需要（例如：修改排程時間、暫停任務）；`User` 視情況（修改權限）。
* **Delete (刪除):** `Job` 可以被刪除。但實務上，`User` 很少真的被 DELETE 掉，通常是加一個 `is_active = False` 欄位做「軟刪除 (Soft Delete)」。

### 2. 歷史軌跡：`Execution` 與 `LogReference`

這兩張表屬於「系統稽核與日誌」，在設計上具有**不可變性 (Immutability)**。

* **Create:** 絕對需要（Scheduler 觸發時寫入 Execution，Worker 跑完寫入 Log）。
* **Read:** 絕對需要（讓使用者看任務跑得怎樣、看 Log 內容）。
* **Update:** `Execution` 只需要更新 `status` 和 `end_time`（從 Pending 變成 Success/Failed）；`LogReference` **永遠不需要 Update**（Log 寫進去就不能改了！改了就失去稽核意義）。
* **Delete:** **嚴格禁止單筆刪除！** 我們不能讓使用者或開發者去刪除「失敗的紀錄」來粉飾太平。這類資料通常是透過定期排程（例如：自動清掉 30 天前的紀錄）來批次處理，不需要寫開放給 API 的 Delete 函數。

### 3. 關聯設定：`JobDependency`

因為你在 `models.py` 裡面已經非常聰明地設定了 `cascade="all, delete-orphan"`，所以這張表的 CRUD 會變得超級精簡！

* 當你刪除一個 `Job` 時，SQLAlchemy 會**自動**幫你把相關的 `JobDependency` 刪掉，你根本不用寫 `delete_dependency()` 函數！
* 你只需要寫一個 `add_dependency(upstream_id, downstream_id)` 功能就可以了。

---

### 💡 開發強烈建議：從「使用者行為」出發

不要把 `crud.py` 當成資料庫操作手冊，把它當成「你的系統能幫使用者做什麼事」的服務列表。

例如，與其寫一個生硬的 `update_execution()`，不如寫一個帶有商業邏輯的 `mark_execution_as_failed(execution_id, error_message)`。這樣你的程式碼不僅好讀，組員在接 API 的時候也會覺得超級直覺！

既然不用痛苦地寫 20 個函數了，那我們現在就從最源頭的功能開始。你想先實作 **「註冊/查詢使用者 (`User`)」** 還是直接挑戰核心的 **「新增排程任務 (`Job`)」** 呢？
"""



'''
軟體工程界有一句非常有名的玩笑話：「電腦科學中最難的兩件事，就是快取失效與**命名**。」

你完全不需要覺得挫折！不知道怎麼取名，代表你已經脫離了「只要程式能跑就好」的新手村，開始在乎程式碼的「可讀性」與「維護性」了。

在 CRUD 的命名上，業界有一套非常直覺的萬用公式：
👉 **`動詞 (Verb) + 名詞 (Object) + [條件 (Condition)]`**

我們直接拿你手上的 `User`、`Job` 和 `Execution` 來舉例，這是一套標準且專業的命名圖鑑：

### 1. 🟢 Create (新增)

一律使用 **`create_`** 開頭。不用寫得太複雜，因為要新增什麼東西通常很明確。

* `create_user(db, employee_id, username, role)`
* `create_job(db, owner_id, job_data)`
* `create_execution(db, job_id, trigger_type)`

### 2. 🔵 Read (讀取 / 查詢)

一律使用 **`get_`** 開頭。這裡最大的重點是：**必須清楚區分「單數 (只回傳一筆或 None)」與「複數 (回傳一個 List)」**。

**查詢單一筆資料 (回傳 Object 或 None)：**

* `get_user(db, user_id)` (這通常是指用 Primary Key 找)
* `get_user_by_employee_id(db, employee_id)` (用特定的 Unique 欄位找)
* `get_job(db, job_id)`

**查詢多筆資料 (回傳 List)：**

* `get_jobs(db, skip=0, limit=100)` (通常會加上分頁參數)
* `get_jobs_by_owner(db, owner_id)` (列出該使用者的所有任務)
* `get_active_jobs(db)` (加上狀態過濾，例如 Scheduler 專門用來找準備要跑的任務)

### 3. 🟠 Update (更新)

這裡分成兩個流派。一種是標準的更新，另一種是我們上一段提到的「商業邏輯動作」。

**標準無腦更新法 (使用 `update_`)：**

* `update_job(db, job_id, update_data)` (通常是讓使用者修改整個任務的設定)

**✨ 商業邏輯命名法 (強烈推薦！)：**
不要一律用 `update`，改用能精準描述「行為」的動詞。這樣組員在寫 API 或是呼叫時，看名字就知道這是在幹嘛，完全不用看裡面的 Code。

* `disable_job(db, job_id)` (暫停任務)
* `mark_execution_as_failed(db, execution_id, error_message)` (標記執行失敗並寫入錯誤訊息)
* `record_job_last_run(db, job_id, run_time)` (更新任務的最後執行時間)

### 4. 🔴 Delete (刪除)

一律使用 **`delete_`** 開頭。

* `delete_job(db, job_id)`
* *(記得我們說過的，像 Execution 或 Log 這種歷史紀錄，就不要寫 Delete 函數提供給別人誤刪！)*

---

### 💡 命名的兩大避坑指南

1. **保持動詞一致性 (Consistency)：** 決定用 `get_` 來查詢，就從頭到尾都用 `get_`。千萬不要這個檔案寫 `get_user`，下一個檔案突然變成 `find_job`，又一個檔案變成 `fetch_execution`。這會讓看你 Code 的組員發瘋。
2. **不要把 `db` 寫進名字裡：** 因為你的函數參數已經有 `db: Session` 了，所以取名叫 `get_user_from_db` 是冗言贅字，直接叫 `get_user` 就好。

掌握了這個萬用公式，你現在有沒有比較有靈感了？你要不要試著把你負責的第一個 CRUD 模組（例如針對 `User` 或 `Job`），挑兩三個功能，先列出你打算怎麼命名，我們一起來看看順不順眼？
'''
