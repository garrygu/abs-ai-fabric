## 📚 **Database Structure Documentation:**

### **1. Primary Database Schema**
- **`postgres-init/01-init-integrated.sql`** - The actual SQL schema file with all table definitions
- **`Data_Objects_Storage_Mapping.md`** - Detailed mapping of what data goes where

### **2. Architecture Documentation**
- **`Hybrid_Storage_Strategy.md`** - Complete overview of PostgreSQL + Qdrant + File Storage
- **`PostgreSQL_vs_Qdrant_Use_Cases.md`** - When to use each storage system
- **`Redis_PostgreSQL_Integration_Architecture.md`** - How Redis and PostgreSQL work together

### **3. Setup and Migration Guides**
- **`Phase_1_PostgreSQL_Setup_Guide.md`** - PostgreSQL setup instructions
- **`Migration_Guide_Redis_to_PostgreSQL.md`** - Migration from Redis to PostgreSQL
- **`Integrated_Setup_Guide.md`** - Complete setup for the integrated application

### **4. Operational Documentation**
- **`Document_CRUD_Operations_Guide.md`** - How to perform CRUD operations
- **`Centralized_Document_Hub_Complete_Guide.md`** - Complete architecture guide
- **`Citation_Feature_Documentation.md`** - Detailed citation functionality guide

Let me show you the current database schema from the SQL file:


[1 tool called]

## 🗄️ **Database Tables Overview:**

### **Core Tables:**
1. **`documents`** - Document metadata and file information
2. **`analysis_results`** - Analysis results and AI-generated insights
3. **`document_chunks`** - Text chunks for vector search
4. **`users`** - User management
5. **`user_sessions`** - Session management
6. **`audit_logs`** - Audit trail for compliance

### **Key Features:**
- **UUID Primary Keys** - All tables use UUIDs for unique identification
- **JSONB Metadata** - Flexible metadata storage using PostgreSQL's JSONB
- **Cascade Deletes** - Proper referential integrity
- **Timestamps** - Automatic creation and update timestamps
- **Indexes** - Optimized for common queries