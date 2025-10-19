# ZAVhoz Bot - NEXT STEPS для PHASE 2

**Статус:** ✅ PHASE 1 завершена  
**Начало PHASE 2:** После стабилизации PHASE 1 изменений

---

## 🎯 PHASE 2: HANDLERS & INTEGRATION TESTING

### 📝 План PHASE 2

**Задачи:**
1. Тестирование всех обработчиков (handlers)
2. Интеграционные тесты
3. Миграции БД (Alembic)
4. Мониторинг и метрики

---

## 1️⃣ ТЕСТИРОВАНИЕ ОБРАБОТЧИКОВ (Priority: HIGH)

### Файлы для создания:
```
tests/
├── test_handlers/
│   ├── __init__.py
│   ├── test_start.py         ← /start command handler
│   ├── test_menu.py          ← Menu navigation
│   ├── test_create_request.py ← Request creation flow
│   ├── test_request_actions.py ← Admin actions
│   ├── test_admin.py         ← Admin functions
│   └── test_files.py         ← File upload handlers
```

### Примеры тестов:

```python
# tests/test_handlers/test_start.py
import pytest
from aiogram import types
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_start_handler_creates_user(db_session):
    """Test /start command creates new user"""
    message = AsyncMock(spec=types.Message)
    message.from_user = MagicMock(
        id=123456,
        username="testuser",
        first_name="Test"
    )
    message.reply = AsyncMock()
    
    # Implement handler testing
    # from handlers.start import start_handler
    # await start_handler(message)
    # message.reply.assert_called_once()

@pytest.mark.asyncio  
async def test_start_handler_greets_existing_user(db_session):
    """Test /start command for existing user"""
    # Create existing user first
    # Test that it doesn't create duplicate
    pass
```

### Целевое покрытие:
- ✅ test_start.py: 90%+ handlers/start.py
- ✅ test_menu.py: 85%+ handlers/menu.py
- ✅ test_create_request.py: 85%+ handlers/create_request.py
- ✅ test_request_actions.py: 80%+ handlers/request_actions.py
- ✅ test_admin.py: 85%+ handlers/admin.py
- ✅ test_files.py: 80%+ handlers/files.py

**Итого:** +100+ новых тестов → 150+ всего

---

## 2️⃣ ИНТЕГРАЦИОННЫЕ ТЕСТЫ (Priority: HIGH)

### Файлы для создания:
```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_request_flow.py  ← Full user request workflow
│   ├── test_admin_flow.py    ← Admin workflow
│   └── test_notifications.py ← Notification system
```

### Примеры:

```python
# tests/integration/test_request_flow.py
@pytest.mark.asyncio
async def test_full_request_creation_flow(db_session):
    """Test complete request creation workflow"""
    # 1. User sends /start
    # 2. User selects "Create Request"
    # 3. User fills in all fields
    # 4. User uploads files
    # 5. Request is stored in DB
    # 6. Admin receives notification
    # 7. Admin accepts request
    # 8. User receives status update
    pass

@pytest.mark.asyncio
async def test_request_completion_flow(db_session):
    """Test request completion with comments and photos"""
    pass
```

---

## 3️⃣ МИГРАЦИИ БД - ALEMBIC (Priority: MEDIUM)

### Текущая проблема:
```python
# ❌ ДО: Ручное создание таблиц
def create_tables():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
```

### Решение - Alembic:
```python
# ✅ ПОСЛЕ: Версионированные миграции
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Файлы для создания:
```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_indexes.py
│   └── ...
├── env.py
├── script.py.mako
└── alembic.ini
```

### Команды:
```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Add new column"

# Применить миграции
alembic upgrade head

# Откатить на версию
alembic downgrade -1

# История миграций
alembic history
```

---

## 4️⃣ МОДЕЛЬНОЕ ТЕСТИРОВАНИЕ (Priority: MEDIUM)

### Файлы для создания:
```
tests/
└── test_models/
    ├── __init__.py
    ├── test_user_model.py
    ├── test_request_model.py
    ├── test_comment_model.py
    └── test_file_model.py
```

### Примеры:

```python
# tests/test_models/test_request_model.py
@pytest.mark.asyncio
async def test_request_model_creation(db_session):
    """Test creating request with valid data"""
    user = User(telegram_id=123, username="test")
    db_session.add(user)
    await db_session.commit()
    
    request = Request(
        user_id=user.id,
        title="Fix computer",
        description="Computer not starting",
        location="Room 101",
        priority=Priority.HIGH,
    )
    db_session.add(request)
    await db_session.commit()
    
    result = await db_session.get(Request, request.id)
    assert result.title == "Fix computer"
    assert result.status == Status.OPEN
```

---

## 5️⃣ МОНИТОРИНГ И ЛОГИРОВАНИЕ (Priority: LOW)

### Улучшения логирования:

```python
# ✅ Structured logging
import structlog

logger = structlog.get_logger()

logger.info(
    "request_created",
    user_id=user.id,
    request_id=request.id,
    priority=request.priority
)
```

### Интеграции:

1. **Sentry** для error tracking:
```python
import sentry_sdk
sentry_sdk.init("https://key@sentry.io/project")
```

2. **Prometheus** для метрик:
```python
from prometheus_client import Counter
request_counter = Counter('requests_created', 'Created requests')
```

3. **ELK Stack** для логов (опционально)

---

## 🚀 РЕКОМЕНДУЕМЫЙ ПОРЯДОК

### Week 1-2: Tests Implementation
- [ ] test_handlers/ (100+ тестов)
- [ ] test_models/ (40+ тестов)
- [ ] test_integration/ (20+ тестов)
- [ ] **Целевой coverage:** 85%+

### Week 3: Database
- [ ] Setup Alembic
- [ ] Create initial migration
- [ ] Test rollback/upgrade
- [ ] Update CI pipeline

### Week 4: Monitoring
- [ ] Add structured logging
- [ ] Setup Sentry
- [ ] Add Prometheus metrics
- [ ] Update dashboards

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ PHASE 2

### Coverage Target:
```
handlers/    : 85%+
models/      : 90%+
utils/       : 95%+ (уже сделано в PHASE 1)
database/    : 80%+
────────────────────
TOTAL        : 85%+
```

### Test Count:
```
PHASE 1: 50 tests
PHASE 2: +150 tests
────────────────────
TOTAL:   200 tests ✨
```

### Quality Gates:
```
[✅] Type Hints: 95%+
[✅] Tests: 200+
[✅] Coverage: 85%+
[✅] Linting: 100%
[✅] Security: Full CI/CD
[✅] Documentation: Complete
[✅] DB Migrations: Versioned (Alembic)
[✅] Monitoring: Structured logging + Sentry
```

---

## 📚 RESOURCES

### Useful links:
- [pytest Async Testing](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Testing Guide](https://docs.sqlalchemy.org/en/20/faq/sqlalchemy_orm.html#is-there-a-recommended-session-pattern)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Sentry Python](https://docs.sentry.io/platforms/python/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)

---

## ✅ CHECKPOINTS

**Before starting PHASE 2:**
- [ ] All PHASE 1 changes committed
- [ ] CI/CD pipeline passing
- [ ] Team review completed
- [ ] .env configured locally
- [ ] Local tests passing

**After completing PHASE 2:**
- [ ] 200+ tests passing
- [ ] Coverage ≥ 85%
- [ ] All handlers tested
- [ ] Alembic migrations working
- [ ] Sentry integrated
- [ ] CI/CD fully green

---

## 🎯 SUCCESS CRITERIA

✅ **PHASE 2 Success Means:**
1. All handlers have unit tests
2. Full request workflow tested end-to-end
3. Database migrations versioned with Alembic
4. Coverage ≥ 85% across all modules
5. Structured logging + error tracking
6. CI/CD fully automated
7. Production-ready deployment process

---

**Next Phase Lead:** Review PHASE 1 results  
**Estimated Duration:** 2-3 weeks  
**Team Size:** 1-2 developers  

**Status:** 🟢 Ready to proceed when approved
