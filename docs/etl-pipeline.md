# Buka Amanzi - ETL Pipeline Explained

The ETL (Extract, Transform, Load) process is the heart of this application, responsible for gathering, processing, and storing the data that users see. It's a sophisticated system with both scheduled, automatic runs and options for manual triggering.

### Orchestration

- The entire process is managed by the `DataScheduler` class (`app/services/data_scheduler.py`).
- This scheduler runs polling loops at configured intervals (e.g., every 30 minutes for DWS data) to automatically check for new information.
- It also exposes an API endpoint (`/api/v1/sync/trigger`) that allows for immediate, manual synchronization of different data sources (`dws`, `treasury`, etc.).

### Data Extraction (The 'E' in ETL)

- The core scraping logic for the Department of Water and Sanitation (DWS) data is encapsulated in the `EnhancedDWSMonitor` class (`app/etl/dws.py`).
- It uses the `httpx` library to fetch the HTML content from the DWS dashboard URL: `https://ws.dws.gov.za/pmd/level.aspx`.
- It then uses `BeautifulSoup` to parse the HTML and extract project details from tables or other page elements. It even has fallback methods in case the website's structure changes.

### Change Detection & Transformation (The 'T')

- To avoid unnecessary processing, the system is designed to only act on *changes*.
- The `poll_with_change_detection` method calculates a hash of the newly scraped content and compares it to the hash of the previously fetched content.
- If the hashes are different, it proceeds to process each project (`_process_project`), transforming the raw scraped data into the application's data model.

### Loading & Notification (The 'L')

- The transformed data is then loaded into the database. New projects are created, and existing ones are updated.
- Crucially, every change (creation or update) is logged in a `DataChangeLog` table.
- After a change is saved, the `notification_manager` is called. It publishes the change event to a Redis channel, which triggers the WebSocket push to all connected clients, ensuring the frontend updates in real-time.

This entire pipeline is designed to be resilient, with error handling, retries with exponential backoff, and health monitoring loops.
