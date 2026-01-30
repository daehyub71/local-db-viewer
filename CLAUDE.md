# Local DB Viewer

로컬 데이터베이스 파일을 탐색하고 조회할 수 있는 PySide6 데스크톱 애플리케이션입니다.

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 대상 환경 | 폐쇄망 VDI (인터넷 연결 불가) |
| 기술 스택 | PySide6 + sqlite3 (내장) + PyInstaller |
| 배포 형태 | Portable EXE |

## 지원 데이터베이스

- **SQLite** (.db, .sqlite, .sqlite3) - 현재 지원
- DuckDB (.duckdb) - 향후 지원 예정
- MS Access (.mdb, .accdb) - 향후 지원 예정

## 디렉토리 구조

```
local-db-viewer/
├── app/
│   ├── main.py                     # 진입점
│   ├── ui/                         # UI 레이어
│   │   ├── main_window.py          # 메인 윈도우
│   │   ├── database_tree.py        # DB 트리 (좌측 패널)
│   │   ├── schema_viewer.py        # 스키마 탭
│   │   ├── data_viewer.py          # 데이터 탭
│   │   ├── query_editor.py         # 쿼리 편집기 탭
│   │   └── history_viewer.py       # 히스토리 탭
│   ├── core/                       # 비즈니스 로직
│   │   ├── connectors/
│   │   │   ├── base_connector.py   # 추상 클래스
│   │   │   ├── sqlite_connector.py # SQLite 구현
│   │   │   └── connector_factory.py# 팩토리
│   │   ├── query_executor.py       # 쿼리 실행 (QThread)
│   │   └── export_service.py       # CSV/JSON 내보내기
│   ├── db/
│   │   └── query_history.py        # 쿼리 히스토리 DB
│   └── utils/
│       └── sql_highlighter.py      # SQL 구문 강조
├── resources/
│   ├── styles/
│   │   └── dark_theme.qss
│   └── icons/
├── scripts/
│   └── build_exe.py                # PyInstaller 빌드
├── tests/
├── LocalDBViewer.spec              # PyInstaller 설정
├── requirements.txt
└── CLAUDE.md
```

## 개발 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
# 개발 모드 실행
python app/main.py

# 테스트 실행
pytest tests/ -v

# EXE 빌드
python scripts/build_exe.py
```

## 아키텍처

### 3계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (PySide6)                              │
│  - MainWindow, DatabaseTree, SchemaViewer, DataViewer      │
│  - QueryEditor, HistoryViewer                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│  Business Logic Layer                                       │
│  - BaseConnector (Abstract), SQLiteConnector                │
│  - ConnectorFactory, QueryExecutor, ExportService           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│  Data Layer                                                 │
│  - QueryHistoryDB (SQLite)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 확장 가능한 커넥터 구조

```python
class BaseConnector(ABC):
    def connect(self, file_path: str) -> bool
    def disconnect(self) -> None
    def get_tables(self) -> List[str]
    def get_schema(self, table_name: str) -> TableSchema
    def get_table_data(self, table_name: str, offset: int, limit: int) -> QueryResult
    def execute_query(self, query: str, timeout: int) -> QueryResult
```

새로운 DB 타입 추가 시:
1. `BaseConnector`를 상속받는 새 커넥터 클래스 구현
2. `ConnectorFactory`에 확장자 매핑 추가

## 핵심 기능

1. **DB 파일 탐색** - 파일 탐색기로 .db, .sqlite, .sqlite3 파일 선택
2. **테이블 구조 조회** - 트리 뷰로 테이블/컬럼 표시
3. **스키마 조회** - 컬럼 타입, 제약조건, 인덱스 정보
4. **데이터 조회** - 페이지네이션 지원 (100행 단위)
5. **SQL 쿼리 실행** - 구문 강조, 실행 시간 표시
6. **결과 내보내기** - CSV, JSON 형식
7. **쿼리 히스토리** - 이전 쿼리 저장 및 재사용

## 의존성

- **PySide6** - Qt6 GUI 프레임워크
- **sqlite3** - Python 내장 SQLite 라이브러리
- **PyInstaller** - EXE 패키징

## VDI 환경 배포

```bash
# EXE 빌드
python scripts/build_exe.py

# 결과물
dist/
└── LocalDBViewer.exe  # 단일 실행 파일 (~50-80MB)
```

VDI에 복사 후 바로 실행 가능 (Python 설치 불필요)
