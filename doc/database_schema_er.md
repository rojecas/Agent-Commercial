# Diagrama de Entidad-Relación (Base de Datos)

Este documento contiene la estructura relacional de la base de datos principal (`MySQL`), diseñada para soportar Multi-Tenant (Múltiples empresas SaaS) y un histórico detallado de conversaciones de ventas impulsadas por la IA.

```mermaid
erDiagram
    users ||--o{ conversations : "has"
    users ||--o{ leads_opportunities : "creates"
    conversations ||--o{ messages : "contains"
    leads_opportunities ||--o{ opportunity_product_recommendations : "receives"

    users {
        BigInteger id PK
        String full_name
        String email
        String phone_number
        String company_name
        String platform "e.g., telegram, whatsapp"
        String platform_user_id
        Text problem_statement
        String tenant_id
        Boolean is_deleted
        DateTime deleted_at
        DateTime created_at
        DateTime updated_at
    }

    conversations {
        BigInteger id PK
        BigInteger user_id FK
        String status "active, closed, handed_off"
        String intent_category "sales, support"
        String tenant_id
        Boolean is_deleted
        DateTime deleted_at
        DateTime created_at
        DateTime updated_at
    }

    messages {
        BigInteger id PK
        BigInteger conversation_id FK
        String role "user, assistant, system"
        Text content "Literal transcript"
        String tenant_id
        DateTime created_at
        DateTime updated_at
    }

    leads_opportunities {
        BigInteger id PK
        BigInteger user_id FK
        String status "qualified, needs_expert, closed"
        Text problem_statement
        String tenant_id
        Boolean is_deleted
        DateTime deleted_at
        DateTime created_at
        DateTime updated_at
    }

    opportunity_product_recommendations {
        BigInteger id PK
        BigInteger opportunity_id FK
        String product_sku
        String product_name
        Text justification "Bot reasoning"
        String tenant_id
        DateTime created_at
        DateTime updated_at
    }
```
