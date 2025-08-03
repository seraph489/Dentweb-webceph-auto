# 데이터 모델 (ERD) - v2.0 (로컬 파일 기반)

## 1. 개요
본 시스템은 클라우드 데이터베이스 대신 로컬 파일 시스템을 사용하여 설정과 데이터를 관리합니다. ERD는 이러한 파일 간의 논리적 관계를 표현합니다.

## 2. ERD 다이어그램

```mermaid
erDiagram
    CONFIG_JSON ||--|{ SETTINGS : "contains"
    EXECUTION --|| MAIN_PY : "is controlled by"
    MAIN_PY --|{ LOG_FILE : "writes to"
    MAIN_PY ..> CONFIG_JSON : "reads"
    MAIN_PY ..> MOUSE_POSITIONS_JSON : "reads"

    EXECUTION }|..|{ TEMP_IMAGES : "creates"
    EXECUTION }|..|{ REPORTS_PDF : "creates"

    SETTINGS {
        string webceph_id
        string webceph_pw
        string upstage_api_key
        string webhook_url
    }

    CONFIG_JSON {
        string filePath "config/config.json"
    }

    MOUSE_POSITIONS_JSON {
        string filePath "config/mouse_positions.json"
        json positions "Coordinates for UI elements"
    }

    MAIN_PY {
        string script "main.py"
        string description "Main control script"
    }

    TEMP_IMAGES {
        string directory "temp_images/{patient_name}/"
        string files "Copied image files"
    }

    REPORTS_PDF {
        string directory "Reports/"
        string file_format "{patient}_{id}_{date}.pdf"
    }

    LOG_FILE {
        string file "app.log"
        string content "Timestamped execution logs"
    }
```

## 3. 엔티티 설명
-   **CONFIG_JSON**: 사용자의 모든 설정(ID, PW, API 키 등)을 저장하는 핵심 설정 파일.
-   **MOUSE_POSITIONS_JSON**: `pyautogui`가 사용할 마우스 좌표를 저장하는 설정 파일.
-   **MAIN_PY**: 전체 자동화 로직을 제어하는 메인 실행 스크립트.
-   **TEMP_IMAGES**: 덴트웹에서 복사한 환자 사진을 WebCeph에 업로드하기 전 임시로 저장하는 폴더.
-   **REPORTS_PDF**: WebCeph에서 분석 후 다운로드한 최종 PDF 보고서가 저장되는 폴더.
-   **LOG_FILE**: 프로그램의 모든 실행 이력과 오류를 기록하는 텍스트 파일.
