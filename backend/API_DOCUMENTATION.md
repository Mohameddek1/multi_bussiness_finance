# Multi-Business Finance System API Documentation

## 📚 Table of Contents
1. [Authentication](#authentication)
2. [Transaction Categories](#transaction-categories)
3. [Transactions](#transactions)
4. [Analytics & Reports](#analytics--reports)
5. [Inter-Business Transactions](#inter-business-transactions)
6. [Cash Flow & Balances](#cash-flow--balances)
7. [Repayments](#repayments)
8. [Error Handling](#error-handling)
9. [Postman Test Data](#postman-test-data)

---

## 🔐 Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Base URL:** `http://localhost:8000/api/`

---

# 📂 TRANSACTION CATEGORIES

## 1. List & Create Categories

### **GET** `/api/businesses/{business_id}/categories/`
List all active categories for a business.

**Parameters:**
- `business_id` (URL parameter): Business ID

**Permissions:** 
- Must have access to the business
- Can manage categories

**Response Example:**
```json
[
    {
        "id": 1,
        "name": "Sales Revenue",
        "type": "income",
        "description": "Revenue from sales",
        "is_active": true,
        "created_at": "2025-07-07T10:00:00Z",
        "created_by": {
            "id": 1,
            "username": "john_doe"
        }
    },
    {
        "id": 2,
        "name": "Office Rent",
        "type": "expense",
        "description": "Monthly office rent",
        "is_active": true,
        "created_at": "2025-07-07T10:01:00Z",
        "created_by": {
            "id": 1,
            "username": "john_doe"
        }
    }
]
```

### **POST** `/api/businesses/{business_id}/categories/`
Create a new category for a business.

**Request Body:**
```json
{
    "name": "Equipment Purchase",
    "type": "expense",
    "description": "Purchasing office equipment and machinery"
}
```

**Field Details:**
- `name` (string, required): Category name (max 100 characters)
- `type` (string, required): Category type - "income", "expense", or "both"
- `description` (string, optional): Category description (max 500 characters)

**Success Response (201):**
```json
{
    "id": 15,
    "name": "Equipment Purchase",
    "type": "expense",
    "description": "Purchasing office equipment and machinery",
    "is_active": true,
    "created_at": "2025-07-07T10:30:00Z",
    "created_by": {
        "id": 1,
        "username": "john_doe"
    }
}
```

---

## 2. Category Details

### **GET** `/api/businesses/{business_id}/categories/{category_id}/`
Retrieve a specific category.

**Parameters:**
- `business_id` (URL): Business ID
- `category_id` (URL): Category ID

**Response Example:**
```json
{
    "id": 5,
    "name": "Marketing",
    "type": "expense",
    "description": "Advertising and marketing costs",
    "is_active": true,
    "created_at": "2025-07-07T10:00:00Z",
    "created_by": {
        "id": 1,
        "username": "john_doe"
    }
}
```

### **PUT** `/api/businesses/{business_id}/categories/{category_id}/`
Update a category.

**Request Body:**
```json
{
    "name": "Digital Marketing",
    "description": "Online advertising and digital marketing campaigns"
}
```

**Success Response (200):**
```json
{
    "id": 5,
    "name": "Digital Marketing",
    "type": "expense",
    "description": "Online advertising and digital marketing campaigns",
    "is_active": true,
    "created_at": "2025-07-07T10:00:00Z",
    "created_by": {
        "id": 1,
        "username": "john_doe"
    }
}
```

### **DELETE** `/api/businesses/{business_id}/categories/{category_id}/`
Delete a category (soft delete - sets is_active to false).

**Success Response (204):** No content

---

## 3. Create Default Categories

### **POST** `/api/businesses/{business_id}/categories/create-defaults/`
Create a set of default categories for a new business.

**Permissions:** Only owners and admins can create default categories.

**No Request Body Required**

**Success Response (200):**
```json
{
    "message": "Created 7 default categories",
    "categories": [
        {
            "id": 1,
            "name": "Sales Revenue",
            "type": "income",
            "description": "Revenue from sales"
        },
        {
            "id": 2,
            "name": "Service Revenue",
            "type": "income",
            "description": "Revenue from services"
        },
        {
            "id": 3,
            "name": "Rent",
            "type": "expense",
            "description": "Office or store rent"
        },
        {
            "id": 4,
            "name": "Utilities",
            "type": "expense",
            "description": "Electricity, water, internet"
        },
        {
            "id": 5,
            "name": "Supplies",
            "type": "expense",
            "description": "Office or business supplies"
        },
        {
            "id": 6,
            "name": "Marketing",
            "type": "expense",
            "description": "Advertising and marketing costs"
        },
        {
            "id": 7,
            "name": "Miscellaneous",
            "type": "both",
            "description": "Other income or expenses"
        }
    ]
}
```

**Default Categories Created:**
1. **Sales Revenue** (income)
2. **Service Revenue** (income)
3. **Rent** (expense)
4. **Utilities** (expense)
5. **Supplies** (expense)
6. **Marketing** (expense)
7. **Miscellaneous** (both)

---

# 💰 TRANSACTIONS

## 1. List & Create Transactions

### **GET** `/api/businesses/{business_id}/transactions/`
List all transactions for a business with powerful filtering options.

**Query Parameters (all optional):**
- `start_date` (YYYY-MM-DD): Filter transactions from this date
- `end_date` (YYYY-MM-DD): Filter transactions until this date
- `type` (string): Filter by transaction type ("income" or "expense")
- `category_id` (integer): Filter by category ID
- `min_amount` (decimal): Minimum transaction amount
- `max_amount` (decimal): Maximum transaction amount

**Example URLs:**
```
# Get all transactions
GET /api/businesses/1/transactions/

# Get expenses over $100 in July 2025
GET /api/businesses/1/transactions/?type=expense&min_amount=100&start_date=2025-07-01&end_date=2025-07-31

# Get transactions in Marketing category
GET /api/businesses/1/transactions/?category_id=6

# Get income between $500-$2000
GET /api/businesses/1/transactions/?type=income&min_amount=500&max_amount=2000
```

**Response Example:**
```json
[
    {
        "id": 1,
        "type": "expense",
        "amount": "150.00",
        "description": "Office supplies purchase",
        "date": "2025-07-07",
        "reference_number": "INV-2025-001",
        "category": {
            "id": 5,
            "name": "Supplies",
            "type": "expense"
        },
        "created_by": {
            "id": 1,
            "username": "john_doe"
        },
        "created_at": "2025-07-07T10:30:00Z",
        "updated_at": "2025-07-07T10:30:00Z"
    },
    {
        "id": 2,
        "type": "income",
        "amount": "1500.00",
        "description": "Website development project",
        "date": "2025-07-06",
        "reference_number": "INV-2025-002",
        "category": {
            "id": 2,
            "name": "Service Revenue",
            "type": "income"
        },
        "created_by": {
            "id": 1,
            "username": "john_doe"
        },
        "created_at": "2025-07-06T14:20:00Z",
        "updated_at": "2025-07-06T14:20:00Z"
    }
]
```

### **POST** `/api/businesses/{business_id}/transactions/`
Create a new transaction.

**Request Body:**
```json
{
    "type": "expense",
    "amount": "250.75",
    "category_id": 5,
    "description": "New laptop for development",
    "date": "2025-07-07",
    "reference_number": "PO-2025-015"
}
```

**Field Details:**
- `type` (string, required): "income" or "expense"
- `amount` (decimal, required): Transaction amount (positive number)
- `category_id` (integer, required): Valid category ID for this business
- `description` (string, required): Transaction description (max 500 characters)
- `date` (date, required): Transaction date (YYYY-MM-DD format)
- `reference_number` (string, optional): External reference number (max 50 characters)

**Success Response (201):**
```json
{
    "id": 25,
    "type": "expense",
    "amount": "250.75",
    "description": "New laptop for development",
    "date": "2025-07-07",
    "reference_number": "PO-2025-015",
    "category": {
        "id": 5,
        "name": "Supplies",
        "type": "expense"
    },
    "business": {
        "id": 1,
        "name": "Tech Solutions Inc"
    },
    "created_by": {
        "id": 1,
        "username": "john_doe"
    },
    "created_at": "2025-07-07T11:15:00Z",
    "updated_at": "2025-07-07T11:15:00Z"
}
```

**Role-Based Restrictions:**
- **Staff users** can only create income transactions
- **Admin/Owner users** can create both income and expense transactions

---

## 2. Transaction Details

### **GET** `/api/businesses/{business_id}/transactions/{transaction_id}/`
Retrieve a specific transaction.

**Parameters:**
- `business_id` (URL): Business ID
- `transaction_id` (URL): Transaction ID

**Response Example:**
```json
{
    "id": 25,
    "type": "expense",
    "amount": "250.75",
    "description": "New laptop for development",
    "date": "2025-07-07",
    "reference_number": "PO-2025-015",
    "category": {
        "id": 5,
        "name": "Supplies",
        "type": "expense",
        "description": "Office or business supplies"
    },
    "business": {
        "id": 1,
        "name": "Tech Solutions Inc"
    },
    "created_by": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
    },
    "created_at": "2025-07-07T11:15:00Z",
    "updated_at": "2025-07-07T11:15:00Z"
}
```

### **PUT** `/api/businesses/{business_id}/transactions/{transaction_id}/`
Update a transaction.

**Request Body:**
```json
{
    "amount": "275.50",
    "description": "New laptop for development (upgraded model)",
    "reference_number": "PO-2025-015-UPDATED"
}
```

**Success Response (200):**
```json
{
    "id": 25,
    "type": "expense",
    "amount": "275.50",
    "description": "New laptop for development (upgraded model)",
    "date": "2025-07-07",
    "reference_number": "PO-2025-015-UPDATED",
    "category": {
        "id": 5,
        "name": "Supplies",
        "type": "expense"
    },
    "business": {
        "id": 1,
        "name": "Tech Solutions Inc"
    },
    "created_by": {
        "id": 1,
        "username": "john_doe"
    },
    "created_at": "2025-07-07T11:15:00Z",
    "updated_at": "2025-07-07T11:45:00Z"
}
```

### **DELETE** `/api/businesses/{business_id}/transactions/{transaction_id}/`
Soft delete a transaction (marks as deleted but keeps in database for audit).

**Success Response (200):**
```json
{
    "detail": "Transaction deleted successfully",
    "deleted_transaction": {
        "id": 25,
        "type": "expense",
        "amount": "275.50",
        "description": "New laptop for development (upgraded model)",
        "deleted_at": "2025-07-07T12:00:00Z",
        "deleted_by": "john_doe"
    }
}
```

---

# 📊 ANALYTICS & REPORTS

## 1. Transaction Summary

### **GET** `/api/businesses/{business_id}/summary/`
Get comprehensive financial summary for a business.

**Query Parameters (optional):**
- `start_date` (YYYY-MM-DD): Start date for summary (default: first day of current month)
- `end_date` (YYYY-MM-DD): End date for summary (default: today)

**Example URLs:**
```
# Current month summary
GET /api/businesses/1/summary/

# Custom date range
GET /api/businesses/1/summary/?start_date=2025-06-01&end_date=2025-06-30

# Year-to-date summary
GET /api/businesses/1/summary/?start_date=2025-01-01
```

**Response Example:**
```json
{
    "total_income": "15750.00",
    "total_expenses": "8200.50",
    "net_amount": "7549.50",
    "transaction_count": 42,
    "period_start": "2025-07-01",
    "period_end": "2025-07-07",
    "income_by_category": {
        "Sales Revenue": "8500.00",
        "Service Revenue": "6250.00",
        "Miscellaneous": "1000.00"
    },
    "expenses_by_category": {
        "Rent": "2500.00",
        "Utilities": "450.50",
        "Supplies": "1200.00",
        "Marketing": "3000.00",
        "Miscellaneous": "1050.00"
    }
}
```

---

## 2. Business Audit Log

### **GET** `/api/businesses/{business_id}/audit-log/`
Get audit trail for a business (last 50 entries).

**Permissions:** Only owners and admins can view audit logs.

**Response Example:**
```json
[
    {
        "id": 1,
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com"
        },
        "action": "create",
        "entity_type": "transaction",
        "entity_id": 25,
        "details": {
            "type": "expense",
            "amount": "250.75",
            "category": "Supplies"
        },
        "timestamp": "2025-07-07T11:15:00Z",
        "ip_address": "192.168.1.100"
    },
    {
        "id": 2,
        "user": {
            "id": 2,
            "username": "jane_admin",
            "email": "jane@example.com"
        },
        "action": "update",
        "entity_type": "category",
        "entity_id": 5,
        "details": {
            "name": "Digital Marketing",
            "previous_name": "Marketing"
        },
        "timestamp": "2025-07-07T10:30:00Z",
        "ip_address": "192.168.1.101"
    },
    {
        "id": 3,
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com"
        },
        "action": "delete",
        "entity_type": "transaction",
        "entity_id": 23,
        "details": {
            "type": "expense",
            "amount": "75.00",
            "description": "Office lunch"
        },
        "timestamp": "2025-07-07T09:45:00Z",
        "ip_address": "192.168.1.100"
    }
]
```

**Tracked Actions:**
- `create`: New records created
- `update`: Records modified
- `delete`: Records deleted (soft delete)
- `login`: User login events
- `permission_change`: Role/permission changes

---

## 3. Export Transactions

### **GET** `/api/businesses/{business_id}/export/`
Export transactions (placeholder for CSV functionality).

**Response Example:**
```json
{
    "message": "CSV export functionality coming soon",
    "download_url": "/api/businesses/1/transactions/export.csv"
}
```

**Note:** This is currently a placeholder. Full CSV export implementation would include:
- Filtered transaction data in CSV format
- Proper CSV headers
- Date range filtering
- Category filtering

---

# 🏢 INTER-BUSINESS TRANSACTIONS

## 1. List & Create Inter-Business Transactions

### **GET** `/api/inter-business-transactions/`
List inter-business transactions for user's businesses.

**Query Parameters (optional):**
- `type` (string): Filter by transaction type ("loan", "transfer", "shared_expense")
- `status` (string): Filter by status ("pending", "completed", "partially_paid")
- `from_business` (integer): Filter by sending business ID
- `to_business` (integer): Filter by receiving business ID
- `start_date` (YYYY-MM-DD): Filter from this date
- `end_date` (YYYY-MM-DD): Filter until this date

**Example URLs:**
```
# All inter-business transactions
GET /api/inter-business-transactions/

# Only loans
GET /api/inter-business-transactions/?type=loan

# Pending transactions between specific businesses
GET /api/inter-business-transactions/?from_business=1&to_business=2&status=pending
```

**Response Example:**
```json
[
    {
        "id": 1,
        "transaction_type": "loan",
        "amount": "5000.00",
        "amount_paid": "1500.00",
        "remaining_balance": "3500.00",
        "status": "partially_paid",
        "purpose": "Equipment purchase funding",
        "date": "2025-07-01",
        "due_date": "2025-12-01",
        "interest_rate": "5.00",
        "from_business": {
            "id": 1,
            "name": "Tech Solutions Inc"
        },
        "to_business": {
            "id": 2,
            "name": "Marketing Pros LLC"
        },
        "created_by": {
            "id": 1,
            "username": "john_doe"
        },
        "created_at": "2025-07-01T09:00:00Z"
    },
    {
        "id": 2,
        "transaction_type": "transfer",
        "amount": "2000.00",
        "amount_paid": "2000.00",
        "remaining_balance": "0.00",
        "status": "completed",
        "purpose": "Cash flow support",
        "date": "2025-07-05",
        "due_date": null,
        "interest_rate": null,
        "from_business": {
            "id": 1,
            "name": "Tech Solutions Inc"
        },
        "to_business": {
            "id": 3,
            "name": "Consulting Co"
        },
        "created_by": {
            "id": 1,
            "username": "john_doe"
        },
        "created_at": "2025-07-05T14:30:00Z"
    }
]
```

### **POST** `/api/inter-business-transactions/`
Create a new inter-business transaction.

**Request Body for Loan:**
```json
{
    "transaction_type": "loan",
    "from_business_id": 1,
    "to_business_id": 2,
    "amount": "10000.00",
    "purpose": "Equipment purchase funding",
    "date": "2025-07-07",
    "due_date": "2025-12-07",
    "interest_rate": "4.5"
}
```

**Request Body for Transfer:**
```json
{
    "transaction_type": "transfer",
    "from_business_id": 1,
    "to_business_id": 3,
    "amount": "3000.00",
    "purpose": "Cash flow support",
    "date": "2025-07-07"
}
```

**Field Details:**
- `transaction_type` (string, required): "loan", "transfer", or "shared_expense"
- `from_business_id` (integer, required): Sending business ID
- `to_business_id` (integer, required): Receiving business ID
- `amount` (decimal, required): Transaction amount
- `purpose` (string, required): Purpose/description
- `date` (date, required): Transaction date
- `due_date` (date, optional): Due date for loans
- `interest_rate` (decimal, optional): Interest rate for loans

**Success Response (201):**
```json
{
    "id": 5,
    "transaction_type": "loan",
    "amount": "10000.00",
    "amount_paid": "0.00",
    "remaining_balance": "10000.00",
    "status": "pending",
    "purpose": "Equipment purchase funding",
    "date": "2025-07-07",
    "due_date": "2025-12-07",
    "interest_rate": "4.50",
    "from_business": {
        "id": 1,
        "name": "Tech Solutions Inc"
    },
    "to_business": {
        "id": 2,
        "name": "Marketing Pros LLC"
    },
    "created_by": {
        "id": 1,
        "username": "john_doe"
    },
    "created_at": "2025-07-07T15:30:00Z"
}
```

**Automatic Actions Performed:**
1. **Balance Update**: Updates inter-business balance between the two businesses
2. **Linked Transactions**: Creates corresponding expense (sender) and income (receiver) transactions
3. **Category Creation**: Auto-creates "Inter-Business Transfer" category if needed
4. **Audit Logging**: Records the action in audit logs

---

## 2. Inter-Business Transaction Details

### **GET** `/api/inter-business-transactions/{transaction_id}/`
Retrieve a specific inter-business transaction.

**Response Example:**
```json
{
    "id": 5,
    "transaction_type": "loan",
    "amount": "10000.00",
    "amount_paid": "2500.00",
    "remaining_balance": "7500.00",
    "status": "partially_paid",
    "purpose": "Equipment purchase funding",
    "date": "2025-07-07",
    "due_date": "2025-12-07",
    "interest_rate": "4.50",
    "from_business": {
        "id": 1,
        "name": "Tech Solutions Inc",
        "owner": "john_doe"
    },
    "to_business": {
        "id": 2,
        "name": "Marketing Pros LLC",
        "owner": "john_doe"
    },
    "created_by": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
    },
    "created_at": "2025-07-07T15:30:00Z",
    "updated_at": "2025-07-07T15:30:00Z"
}
```

### **PUT** `/api/inter-business-transactions/{transaction_id}/`
Update an inter-business transaction.

**Request Body:**
```json
{
    "purpose": "Equipment purchase and setup funding",
    "due_date": "2025-11-30",
    "interest_rate": "4.25"
}
```

### **DELETE** `/api/inter-business-transactions/{transaction_id}/`
Soft delete an inter-business transaction.

**Success Response (204):** No content

---

# 💰 CASH FLOW & BALANCES

## 1. Business Cash Flow Summary

### **GET** `/api/businesses/{business_id}/cash-flow/`
Get comprehensive cash flow summary for a business.

**Query Parameters (optional):**
- `start_date` (YYYY-MM-DD): Start date (default: first day of current month)
- `end_date` (YYYY-MM-DD): End date (default: today)

**Response Example:**
```json
{
    "business_id": 1,
    "business_name": "Tech Solutions Inc",
    "money_received": "12500.00",
    "money_sent": "8000.00",
    "net_inter_business_flow": "4500.00",
    "total_owed_to_others": "3500.00",
    "total_owed_by_others": "7500.00",
    "net_balance": "4000.00",
    "active_loans_given": 2,
    "active_loans_received": 1,
    "pending_repayments": 3
}
```

**Field Explanations:**
- `money_received`: Total money received from other businesses in the period
- `money_sent`: Total money sent to other businesses in the period
- `net_inter_business_flow`: Net flow (received - sent) for the period
- `total_owed_to_others`: Total amount this business owes to others
- `total_owed_by_others`: Total amount others owe to this business
- `net_balance`: Net balance (positive = others owe you, negative = you owe others)
- `active_loans_given`: Number of active loans this business has given
- `active_loans_received`: Number of active loans this business has received
- `pending_repayments`: Number of overdue repayments

---

## 2. Inter-Business Balances

### **GET** `/api/inter-business-balances/`
Get all inter-business balances for user's businesses.

**Response Example:**
```json
[
    {
        "id": 1,
        "business_a": {
            "id": 1,
            "name": "Tech Solutions Inc"
        },
        "business_b": {
            "id": 2,
            "name": "Marketing Pros LLC"
        },
        "net_balance": "3500.00",
        "balance_explanation": "Tech Solutions Inc owes Marketing Pros LLC $3,500.00",
        "last_updated": "2025-07-07T15:30:00Z"
    },
    {
        "id": 2,
        "business_a": {
            "id": 1,
            "name": "Tech Solutions Inc"
        },
        "business_b": {
            "id": 3,
            "name": "Consulting Co"
        },
        "net_balance": "-2000.00",
        "balance_explanation": "Consulting Co owes Tech Solutions Inc $2,000.00",
        "last_updated": "2025-07-06T10:15:00Z"
    }
]
```

**Balance Interpretation:**
- **Positive balance**: business_a owes money to business_b
- **Negative balance**: business_b owes money to business_a
- **Zero balance**: No outstanding debt between businesses (excluded from response)

---

# 💸 REPAYMENTS

## 1. Make Repayment

### **POST** `/api/repayments/`
Record a repayment for an inter-business loan.

**Request Body:**
```json
{
    "inter_transaction_id": 5,
    "amount": "2500.00",
    "payment_date": "2025-07-07"
}
```

**Field Details:**
- `inter_transaction_id` (integer, required): ID of the inter-business transaction being repaid
- `amount` (decimal, required): Repayment amount
- `payment_date` (date, required): Date of payment

**Success Response (200):**
```json
{
    "message": "Repayment recorded successfully",
    "transaction_id": 5,
    "amount_paid": "2500.00",
    "remaining_balance": "7500.00",
    "status": "partially_paid"
}
```

**Automatic Actions Performed:**
1. **Transaction Update**: Updates amount_paid and status of inter-business transaction
2. **Balance Adjustment**: Updates inter-business balance between the businesses
3. **Transaction Records**: Creates expense transaction (paying business) and income transaction (receiving business)
4. **Reference Numbers**: Uses format "REP-{transaction_id}" for tracking

**Validations:**
- Payment amount cannot exceed remaining balance
- User must have access to both businesses involved
- Inter-business transaction must exist and not be deleted

**Error Responses:**
```json
// Payment exceeds remaining balance
{
    "error": "Payment amount (3000.00) exceeds remaining balance (2500.00)"
}

// Transaction not found
{
    "error": "Transaction not found"
}

// Access denied
{
    "error": "Access denied"
}
```

---

## 2. Overdue Payments

### **GET** `/api/overdue-payments/`
Get all overdue payments for user's businesses.

**Response Example:**
```json
[
    {
        "id": 3,
        "transaction_type": "loan",
        "amount": "5000.00",
        "amount_paid": "1000.00",
        "remaining_balance": "4000.00",
        "status": "partially_paid",
        "purpose": "Inventory purchase",
        "date": "2025-05-01",
        "due_date": "2025-06-30",
        "days_overdue": 7,
        "interest_rate": "6.00",
        "from_business": {
            "id": 2,
            "name": "Marketing Pros LLC"
        },
        "to_business": {
            "id": 3,
            "name": "Consulting Co"
        },
        "created_by": {
            "id": 1,
            "username": "john_doe"
        },
        "created_at": "2025-05-01T10:00:00Z"
    }
]
```

**Criteria for Overdue:**
- Transaction type is "loan"
- Status is "pending" or "partially_paid"
- Due date is before today
- Transaction is not deleted

---

# ⚠️ ERROR HANDLING

## HTTP Status Codes

- **200 OK**: Successful GET, PUT requests
- **201 Created**: Successful POST requests
- **204 No Content**: Successful DELETE requests
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

## Common Error Responses

### Validation Errors (400)
```json
{
    "amount": ["This field is required."],
    "category_id": ["Invalid pk \"999\" - object does not exist."],
    "date": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
}
```

### Authentication Errors (401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Permission Errors (403)
```json
{
    "error": "You do not have permission to view audit logs"
}
```

### Not Found Errors (404)
```json
{
    "detail": "Not found."
}
```

---

# 🧪 POSTMAN TEST DATA

## Environment Variables
```json
{
    "base_url": "http://localhost:8000/api",
    "token": "YOUR_JWT_TOKEN_HERE",
    "business_id": "1",
    "category_id": "5",
    "transaction_id": "25",
    "inter_transaction_id": "5"
}
```

## Collection Structure

### 1. Authentication
- **Login**: `POST {{base_url}}/auth/login/`
- **Register**: `POST {{base_url}}/auth/register/`
- **Refresh Token**: `POST {{base_url}}/auth/refresh/`

### 2. Categories
- **List Categories**: `GET {{base_url}}/businesses/{{business_id}}/categories/`
- **Create Category**: `POST {{base_url}}/businesses/{{business_id}}/categories/`
- **Get Category**: `GET {{base_url}}/businesses/{{business_id}}/categories/{{category_id}}/`
- **Update Category**: `PUT {{base_url}}/businesses/{{business_id}}/categories/{{category_id}}/`
- **Delete Category**: `DELETE {{base_url}}/businesses/{{business_id}}/categories/{{category_id}}/`
- **Create Defaults**: `POST {{base_url}}/businesses/{{business_id}}/categories/create-defaults/`

### 3. Transactions
- **List Transactions**: `GET {{base_url}}/businesses/{{business_id}}/transactions/`
- **Create Transaction**: `POST {{base_url}}/businesses/{{business_id}}/transactions/`
- **Get Transaction**: `GET {{base_url}}/businesses/{{business_id}}/transactions/{{transaction_id}}/`
- **Update Transaction**: `PUT {{base_url}}/businesses/{{business_id}}/transactions/{{transaction_id}}/`
- **Delete Transaction**: `DELETE {{base_url}}/businesses/{{business_id}}/transactions/{{transaction_id}}/`

### 4. Analytics
- **Transaction Summary**: `GET {{base_url}}/businesses/{{business_id}}/summary/`
- **Audit Log**: `GET {{base_url}}/businesses/{{business_id}}/audit-log/`
- **Export**: `GET {{base_url}}/businesses/{{business_id}}/export/`

### 5. Inter-Business
- **List Inter-Business**: `GET {{base_url}}/inter-business-transactions/`
- **Create Inter-Business**: `POST {{base_url}}/inter-business-transactions/`
- **Get Inter-Business**: `GET {{base_url}}/inter-business-transactions/{{inter_transaction_id}}/`
- **Cash Flow**: `GET {{base_url}}/businesses/{{business_id}}/cash-flow/`
- **Balances**: `GET {{base_url}}/inter-business-balances/`
- **Make Repayment**: `POST {{base_url}}/repayments/`
- **Overdue Payments**: `GET {{base_url}}/overdue-payments/`

## Sample Test Data

### Create Category
```json
{
    "name": "Software Subscriptions",
    "type": "expense",
    "description": "Monthly software and tool subscriptions"
}
```

### Create Transaction
```json
{
    "type": "expense",
    "amount": "99.99",
    "category_id": 5,
    "description": "Adobe Creative Suite monthly subscription",
    "date": "2025-07-07",
    "reference_number": "SUB-2025-001"
}
```

### Create Inter-Business Loan
```json
{
    "transaction_type": "loan",
    "from_business_id": 1,
    "to_business_id": 2,
    "amount": "15000.00",
    "purpose": "Inventory expansion funding",
    "date": "2025-07-07",
    "due_date": "2025-12-31",
    "interest_rate": "5.5"
}
```

### Make Repayment
```json
{
    "inter_transaction_id": 5,
    "amount": "3000.00",
    "payment_date": "2025-07-07"
}
```

---

## 🔧 Testing Scenarios

### Complete Workflow Test
1. **Setup**: Create default categories
2. **Basic Operations**: Create, read, update, delete transactions
3. **Inter-Business**: Create loans and transfers between businesses
4. **Repayments**: Make partial payments on loans
5. **Analytics**: Check summaries and cash flow
6. **Audit**: Verify all actions are logged

### Permission Testing
1. **Owner**: Test all operations
2. **Admin**: Test all operations except audit logs
3. **Staff**: Test limited operations (income only)
4. **Unauthorized**: Test access denied scenarios

### Edge Cases
1. **Invalid Data**: Test validation errors
2. **Large Amounts**: Test decimal precision
3. **Date Ranges**: Test filtering edge cases
4. **Overdue Loans**: Test overdue calculation
5. **Balance Updates**: Test inter-business balance accuracy

---

This documentation covers every endpoint in the system with complete examples, error handling, and testing guidance. Use this as your complete reference for API integration and testing.
