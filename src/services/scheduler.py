from apscheduler.schedulers.background import BackgroundScheduler
from src.services.scraper import run_scraper_job

scheduler = BackgroundScheduler()

def start_scheduler():
    # Run the job every hour, or adjust as needed
    scheduler.add_job(run_scraper_job, 'interval', minutes=60, id='scraper_job', replace_existing=True)
    scheduler.start()
    print("Background scheduler started.")

def shutdown_scheduler():
    scheduler.shutdown()
    print("Background scheduler shut down.")
