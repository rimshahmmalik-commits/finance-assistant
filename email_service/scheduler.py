import time
from datetime import datetime

from email_service.automation import run_automatic_reminders


CHECK_INTERVAL = 60


def run_scheduler():
    print("Finance Assistant Reminder Scheduler started.")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                "Checking payment reminders..."
            )

            results = run_automatic_reminders()

            if not results:
                print("No reminders require action.")

            else:
                for result in results:
                    print(result)

            print(
                f"Next check in {CHECK_INTERVAL} seconds.\n"
            )

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nReminder Scheduler stopped.")
            break

        except Exception as error:
            print(f"Scheduler error: {error}")
            print("Retrying in 60 seconds...\n")
            time.sleep(60)


if __name__ == "__main__":
    run_scheduler()