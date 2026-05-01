# 데이터 모델 (ERD)

3차 단계 모델. 도메인 책임으로 5개 앱에 분산.

## Mermaid 다이어그램

```mermaid
erDiagram
    User ||--o{ Story : writes
    User ||--o{ Comment : writes
    User ||--o{ Like : creates
    User ||--o{ Bookmark : creates
    Story }o--|| Category : belongs_to
    Story ||--o{ Comment : has
    Comment ||--o{ Comment : replies_to
    Law }o--|| Category : belongs_to
    Precedent }o--|| Category : belongs_to
    Precedent }o--o{ Law : references

    User {
        int id PK
        string username
        string email
        string nickname
        string password_hash
        bool is_active
        bool is_staff
        datetime date_joined
        datetime created_at
        datetime updated_at
    }
    Category {
        int id PK
        string name
        string slug
        text description
        int order
        datetime created_at
    }
    Story {
        int id PK
        int user_id FK
        string title
        text content
        int category_id FK
        bool is_anonymous
        bool is_deleted
        datetime deleted_at
        int view_count
        datetime created_at
        datetime updated_at
    }
    Law {
        int id PK
        string law_name
        string article_number
        string article_title
        text content
        int category_id FK
        string keywords
        url source_url
        bool is_active
        datetime created_at
        datetime updated_at
    }
    Precedent {
        int id PK
        string case_number
        string case_name
        string court
        date judgment_date
        text summary
        text content
        int category_id FK
        string keywords
        url source_url
        string result_type
        datetime created_at
        datetime updated_at
    }
    Comment {
        int id PK
        int user_id FK
        int story_id FK
        int parent_id FK
        text content
        bool is_deleted
        datetime deleted_at
        datetime created_at
        datetime updated_at
    }
    Like {
        int id PK
        int user_id FK
        string target_type
        int target_id
        datetime created_at
    }
    Bookmark {
        int id PK
        int user_id FK
        string target_type
        int target_id
        datetime created_at
    }
```

## 핵심 관계

| 관계 | 카디널리티 | on_delete | 비고 |
|------|----------|-----------|------|
| User → Story.user | 1:N | SET_NULL | 탈퇴 회원 사연은 "탈퇴 회원"으로 표시 |
| User → Comment.user | 1:N | SET_NULL | 동일 |
| User → Like.user | 1:N | CASCADE | 사용자 삭제 시 좋아요도 삭제 |
| User → Bookmark.user | 1:N | CASCADE | 동일 |
| Category → Story.category | 1:N | PROTECT | 카테고리 삭제 시 사연 보호 (삭제 차단) |
| Category → Law.category, Precedent.category | 1:N | SET_NULL | nullable |
| Story → Comment.story | 1:N | CASCADE | 사연 hard delete 시 댓글도 삭제 |
| Comment → Comment.parent | self-FK | CASCADE | 부모 hard delete 시 대댓글 삭제 (1단계만) |
| Precedent ↔ Law | M:N | through related_laws | 한 판례가 여러 법령 인용 |

## Soft Delete

`Story`, `Comment`에 `is_deleted` + `deleted_at` 컬럼.
- 기본 manager (`objects`)는 `is_deleted=False`만 노출
- `all_objects`는 전체 (admin/관리자용)

## 인덱스

- Story: `[-created_at]` 순서, `category` 필터, `view_count` 정렬
- Comment: `(story, created_at)` 합성 인덱스, `parent` 인덱스
- Law: `law_name` 인덱스, `category` 인덱스, `(law_name, article_number)` unique
- Precedent: `(court, -judgment_date)` 합성 인덱스, `category` 인덱스, `(case_number, court)` unique
- Like / Bookmark: `(user, target_type, target_id)` unique, `(target_type, target_id)` 인덱스
