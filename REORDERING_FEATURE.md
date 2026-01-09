# Indicator Reordering Feature

## Overview
The macro indicators application includes a comprehensive admin feature that allows administrators to reorder indicators across all category pages. The display order is persisted in the database and automatically applied throughout the application.

## Architecture

### Database Schema
The `display_order` field is stored in the `indicators` table:

```python
# backend/app/models.py
class Indicator(Base):
    # ... other fields ...
    display_order = Column(Integer, default=0)
```

### Backend Implementation

#### 1. Admin Reorder Endpoint
**File**: `backend/app/routers/admin.py`

```python
@router.post("/reorder-indicators")
def reorder_indicators(
    indicator_orders: List[dict],
    admin_token: str = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Update display order for multiple indicators
    
    Expected format: [{"slug": "indicator-slug", "display_order": 0}, ...]
    """
```

**Request Format**:
```json
POST /api/admin/reorder-indicators?admin_token=admin
Content-Type: application/json

[
  {"slug": "gold-price", "display_order": 0},
  {"slug": "silver-price", "display_order": 1},
  {"slug": "oil-price", "display_order": 2}
]
```

#### 2. Ordered Queries
All indicator queries now respect the `display_order` field:

**Categories Router** (`backend/app/routers/categories.py`):
```python
# Get indicators ordered by display_order
ordered_indicators = db.query(Indicator).filter(
    Indicator.category_id == category.id
).order_by(Indicator.display_order, Indicator.id).all()
```

**Indicators Router** (`backend/app/routers/indicators.py`):
```python
query = db.query(Indicator)
if category_slug:
    query = query.join(Category).filter(Category.slug == category_slug)
return query.order_by(Indicator.display_order).all()
```

### Frontend Implementation

#### Admin Dashboard UI
**File**: `frontend/src/app/admin/dashboard/page.tsx`

The admin dashboard includes a dedicated reordering interface:

1. **Reorder Button**: Activates the reordering mode
2. **Up/Down Arrows**: Move indicators up or down in the list
3. **Save Order Button**: Persists changes to the database

**Key Features**:
- Visual feedback with position numbers (#1, #2, etc.)
- Disabled state for boundary buttons (can't move first item up, etc.)
- Loading state during save operation
- Success/error notifications

**State Management**:
```typescript
const [reorderedIndicators, setReorderedIndicators] = useState<Array<any>>([]);
const [isSavingOrder, setIsSavingOrder] = useState(false);

const moveIndicator = (index: number, direction: 'up' | 'down') => {
  const newIndicators = [...reorderedIndicators];
  const targetIndex = direction === 'up' ? index - 1 : index + 1;
  
  if (targetIndex >= 0 && targetIndex < newIndicators.length) {
    [newIndicators[index], newIndicators[targetIndex]] = 
      [newIndicators[targetIndex], newIndicators[index]];
    setReorderedIndicators(newIndicators);
  }
};
```

## User Workflow

### Accessing the Reorder Feature

1. **Login to Admin Panel**
   - Navigate to: `http://localhost:3000/admin` (or your production URL)
   - Enter admin token: `admin` (default, should be changed in production)

2. **Navigate to Dashboard**
   - After successful login, you'll be redirected to `/admin/dashboard`

3. **Activate Reorder Mode**
   - Click the purple "Reorder" button in the "Manage Data" section
   - The reordering interface will appear

4. **Reorder Indicators**
   - Each indicator shows its current position (#1, #2, #3, etc.)
   - Click ↑ to move an indicator up in the list
   - Click ↓ to move an indicator down in the list
   - The list updates in real-time as you reorder

5. **Save Changes**
   - Click the green "Save Order" button
   - Wait for the success confirmation
   - The new order is now active across all pages

6. **Cancel/Exit**
   - Click "Cancel" to exit without saving
   - Your original order will be preserved

## Pages Affected by Reordering

The reordering affects indicator display on:

1. **Market Indexes** - `/category/market-indexes`
2. **Precious Metals** - `/category/precious-metals`
3. **Energy** - `/category/energy`
4. **Commodities** - `/category/commodities`
5. **Exchange Rates** - `/category/exchange-rates`
6. **Interest Rates** - `/category/interest-rates`
7. **Economy** - `/category/economy`
8. **Admin Dashboard** - Indicators list table
9. **API Endpoints** - All indicator queries

## API Reference

### Get Categories with Ordered Indicators
```http
GET /api/categories/{slug}
```

**Response**:
```json
{
  "id": 1,
  "name": "Market Indexes",
  "slug": "market-indexes",
  "description": "...",
  "display_order": 0,
  "indicators": [
    {
      "id": 1,
      "name": "S&P 500",
      "slug": "sp500",
      "unit": "Index",
      "latest_value": 4500.50,
      "latest_date": "2024-01-15",
      "change_percent": 1.5
    }
    // ... more indicators in display_order
  ]
}
```

### Get All Indicators (Ordered)
```http
GET /api/indicators
```

Returns all indicators ordered by `display_order`.

### Reorder Indicators (Admin)
```http
POST /api/admin/reorder-indicators?admin_token={token}
Content-Type: application/json

[
  {"slug": "indicator-1", "display_order": 0},
  {"slug": "indicator-2", "display_order": 1},
  {"slug": "indicator-3", "display_order": 2}
]
```

**Response**:
```json
{
  "message": "Indicator order updated successfully",
  "updated_count": 3
}
```

## Testing

Run the test script to verify reordering functionality:

```bash
# Make sure backend is running first
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# In another terminal
cd /path/to/project
python test_reorder.py
```

## Security Considerations

1. **Authentication**: The reorder endpoint requires a valid `admin_token`
2. **Production**: Change the default admin token in production environments
3. **Validation**: The endpoint validates all slugs exist before updating

## Future Enhancements

Potential improvements to the reordering system:

1. **Drag and Drop**: Implement drag-and-drop reordering in the UI
2. **Bulk Operations**: Allow reordering within specific categories only
3. **Undo/Redo**: Add undo functionality for accidental changes
4. **Preview**: Show a preview of how the new order will look
5. **Category Reordering**: Also allow reordering of categories themselves
6. **Audit Log**: Track who reordered indicators and when
7. **Role-Based Access**: More granular permissions for different admin roles

## Troubleshooting

### Indicators not showing in new order
- **Solution**: Check that the frontend is fetching fresh data (clear browser cache)
- Verify the API response includes the correct `display_order` values
- Check that indicators are being sorted by `display_order` in the backend query

### Save order fails
- **Solution**: Verify admin token is correct
- Check backend logs for error messages
- Ensure all indicator slugs in the request exist in the database

### Reorder button not visible
- **Solution**: Ensure you're logged in as admin
- Check that the admin stats API call is successful
- Verify you have indicators in the database

## Code References

- Backend Model: [`backend/app/models.py`](../backend/app/models.py) - Line 35
- Backend Router: [`backend/app/routers/admin.py`](../backend/app/routers/admin.py) - Line 557
- Categories Router: [`backend/app/routers/categories.py`](../backend/app/routers/categories.py) - Line 19
- Indicators Router: [`backend/app/routers/indicators.py`](../backend/app/routers/indicators.py) - Line 28
- Frontend UI: [`frontend/src/app/admin/dashboard/page.tsx`](../frontend/src/app/admin/dashboard/page.tsx) - Line 1143

