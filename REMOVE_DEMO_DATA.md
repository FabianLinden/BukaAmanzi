# Remove Demo Data - Switch to Real-Time Only

This guide will help you completely remove all demo/mock data from your BukaAmanzi system and configure it to use only real-time data from official government APIs.

## What This Does

🗑️ **Removes:**
- Demo municipalities (like "Demo Municipality", "DEMO-001")
- Demo projects (like external_id="EXT-123")
- Mock financial data (flagged with `_mock_data: true`)
- Demo data generation code references

✅ **Keeps:**
- Real municipalities from Treasury API
- Real projects from DWS API
- Real financial data from government sources
- All real-time data functionality

## Quick Start

### Option 1: Using the Comprehensive Script (Recommended)

1. **Run the demo data removal script:**
   ```bash
   python remove_demo_data.py
   ```

   If you get dependency errors, install them first:
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   python remove_demo_data.py
   ```

### Option 2: Using the Backend-Specific Script

1. **Run the backend cleanup script:**
   ```bash
   cd backend
   python cleanup_demo_data.py
   ```

## What's Been Changed

### 1. Backend Code Changes ✅ 

- **`backend/app/main.py`**: Disabled automatic demo data seeding on startup
- **`backend/app/etl/treasury.py`**: Removed DEMO-001 from mock data generation
- **`backend/cleanup_demo_data.py`**: Enhanced to remove ALL demo data types

### 2. Demo Data Removal ⏳

The scripts will remove:
- Any municipality with "Demo", "Test", or "Sample" in the name
- Municipality code "DEMO-001"
- Projects with external_id="EXT-123"
- Any financial data flagged with `_mock_data: true`

## Verification

After running the cleanup, you should see:

```
📊 Real data remaining in system:

🏛️  Municipalities (X):
   ✅ City of Cape Town (CPT) - Western Cape
   ✅ eThekwini Municipality (ETH) - KwaZulu-Natal
   ✅ City of Johannesburg (JHB) - Gauteng
   ... and X more

📋 Projects (X):
   ✅ Water Infrastructure Project (dws_api)
   ✅ Sanitation Upgrade Program (dws_api)
   ... and X more

💰 Financial Records (X):
   ✅ City of Cape Town (2023) - Real API
   ✅ eThekwini Municipality (2023) - Real API
   ... and X more
```

## Next Steps

### 1. Restart Your Backend Server
```bash
cd backend
# If using uvicorn directly:
uvicorn app.main:app --reload

# Or however you normally start your backend
```

### 2. Run ETL to Fetch Latest Real Data
```bash
# Fetch latest municipality data from Treasury API
curl -X POST http://localhost:8000/api/v1/etl/treasury/sync

# Fetch latest project data from DWS API  
curl -X POST http://localhost:8000/api/v1/etl/dws/sync
```

### 3. Check Frontend
- Open your frontend application
- Navigate to the municipalities page
- You should now see only real municipalities
- No more "Demo Municipality" or test data

## Data Sources Now Used

📡 **Real-Time Data Sources:**
- **Treasury API**: `municipaldata.treasury.gov.za` - Financial data
- **DWS API**: Department of Water and Sanitation - Project data
- **Other Government APIs**: As configured in your ETL

⚠️ **Fallback Behavior:**
- If real API data is unavailable, the system may still generate mock data as a fallback
- This is only for existing real municipalities, not demo ones
- The mock data is clearly flagged with `_mock_data: true`

## Troubleshooting

### Script Won't Run
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Try running from project root
cd ..
python remove_demo_data.py
```

### No Data After Cleanup
If you have no data at all after cleanup:

1. **Run ETL processes** to fetch real data:
   ```bash
   curl -X POST http://localhost:8000/api/v1/etl/sync-all
   ```

2. **Check ETL logs** for any API connection issues

3. **Manually trigger data sync** from the admin interface

### Database Connection Issues
Make sure your database is running and accessible:
- Check database connection settings in `backend/app/core/config.py`
- Ensure database server is running
- Verify database credentials

## Reverting (If Needed)

If you need to restore demo data for development:

1. **Re-enable seeding** in `backend/app/main.py`:
   ```python
   # Change this line back:
   ids = await seed_database(session)
   ```

2. **Add back DEMO-001** in `treasury.py` if needed

3. **Restart backend** to trigger seeding

## Files Modified

- ✅ `backend/app/main.py` - Disabled demo seeding
- ✅ `backend/app/etl/treasury.py` - Removed DEMO-001 reference  
- ✅ `backend/cleanup_demo_data.py` - Enhanced cleanup
- ✅ `remove_demo_data.py` - New comprehensive script
- ✅ `REMOVE_DEMO_DATA.md` - This instruction file

## Success Indicators

✅ **Demo data removal successful when:**
- No municipalities with "Demo" in the name
- No projects with external_id="EXT-123"  
- No financial records with `_mock_data: true`
- Backend logs show "Demo data seeding disabled"
- Frontend shows only real municipality names

🎉 **Your system now uses only real-time data from official government sources!**
