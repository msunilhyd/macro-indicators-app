# Quick Guide: How to Reorder Indicators

## Step-by-Step Instructions

### 1️⃣ Access the Admin Panel

Open your web browser and navigate to:
```
http://localhost:3000/admin
```
(or your production URL + `/admin`)

### 2️⃣ Login

Enter your admin token and click "Login"
- Default token: `admin` 
- ⚠️ Change this in production!

### 3️⃣ Open the Reorder Interface

Once in the dashboard, look for the purple **"Reorder"** button in the "Manage Data" section and click it.

### 4️⃣ Reorder Your Indicators

You'll see a list of all indicators with their current positions:

```
#1  S&P 500          Market Indexes • 5,432 points  [↑] [↓]
#2  Gold Price       Precious Metals • 3,210 points [↑] [↓]
#3  Crude Oil        Energy • 8,123 points          [↑] [↓]
```

- Click **↑** to move an indicator up in the list
- Click **↓** to move an indicator down in the list
- The numbers update automatically as you reorder

### 5️⃣ Save Your Changes

When you're happy with the new order, click the green **"Save Order"** button at the top.

✅ You'll see a success message: "Order saved successfully"

### 6️⃣ Verify the Changes

Visit any category page to see your new ordering in action:
- http://localhost:3000/category/market-indexes
- http://localhost:3000/category/precious-metals
- http://localhost:3000/category/energy
- etc.

## Tips & Tricks

### 💡 Planning Your Order

Consider ordering indicators by:
- **Importance**: Most critical indicators first
- **Popularity**: Most viewed indicators at the top
- **Logical grouping**: Related indicators together
- **Alphabetical**: For easy scanning

### ⚠️ What to Watch Out For

1. **Don't forget to save**: Changes aren't applied until you click "Save Order"
2. **Global effect**: The order applies to ALL category pages
3. **No undo**: Once saved, you'll need to manually reorder if you made a mistake
4. **Browser refresh**: After saving, refresh any open category pages to see changes

### 🔄 Starting Over

If you mess up while reordering:
- Click **"Cancel"** to exit without saving
- The original order will be preserved
- Click "Reorder" again to start fresh

## Example Scenarios

### Scenario 1: Moving S&P 500 to the Top

**Before:**
```
#1  Gold Price
#2  Silver Price  
#3  S&P 500       ← Want to move this to #1
```

**Actions:**
1. Click ↑ on "S&P 500" → Moves to #2
2. Click ↑ on "S&P 500" again → Moves to #1

**After:**
```
#1  S&P 500
#2  Gold Price
#3  Silver Price
```

### Scenario 2: Moving Crude Oil Down

**Before:**
```
#1  Crude Oil      ← Want to move this to #3
#2  Natural Gas
#3  Heating Oil
```

**Actions:**
1. Click ↓ on "Crude Oil" → Moves to #2
2. Click ↓ on "Crude Oil" again → Moves to #3

**After:**
```
#1  Natural Gas
#2  Heating Oil
#3  Crude Oil
```

## Need Help?

- **Backend not running?** 
  ```bash
  cd backend
  source venv/bin/activate
  uvicorn app.main:app --reload --port 8000
  ```

- **Can't save order?**
  - Check that your admin token is correct
  - Look at the browser console for error messages
  - Verify the backend is running and accessible

- **Changes not showing?**
  - Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
  - Clear browser cache
  - Check the API response in browser dev tools

For more technical details, see [REORDERING_FEATURE.md](REORDERING_FEATURE.md)
