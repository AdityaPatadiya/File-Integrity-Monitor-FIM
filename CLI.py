import os
import argparse

from src.FIM.FIM import monitor_changes
from src.utils.database import database_operation
from src.Authentication.Authentication import Authentication
from src.utils.anomaly_detection import parse_log_file, load_vectorizer_model


class CLI:
    def __init__(self):
        self.monitor_changes = monitor_changes()
        self.authentication = Authentication()
        self.database_operation = database_operation()
        self.exclude_files = []

    def main(self):
        parser = argparse.ArgumentParser(description="File Integrity Monitor CLI Tool")
        parser.add_argument("--monitor", action="store_true", help="Start monitoring multiple directory")
        parser.add_argument("--view-baseline", action="store_true", help="View the current baseline data")
        parser.add_argument("--reset-baseline", action="store_true", help="Reset the baseline data")
        parser.add_argument("--view-logs", action="store_true", help="View the log file")
        parser.add_argument("--analyze-logs", action="store_true", help="Analyze the log file for anomalies")
        parser.add_argument("--exclude", type=str, help="Exclude selected file and folder")
        parser.add_argument("--dir", nargs="+", type=str, help="Add directories to monitor.")

        args = parser.parse_args()
        if args.dir is not None:
            monitored_dirs = [os.path.abspath(dir) for dir in args.dir]

        if args.analyze_logs:
            log_folder_path = 'logs'
            for file in os.listdir(log_folder_path):
                file_path = os.path.join(log_folder_path, file)
                log_df = parse_log_file(file_path)
                if log_df.empty:
                    print("No log data found.")
                else:
                    vectorizer, model = load_vectorizer_model()
                    if vectorizer is None or model is None:
                        print("Model not trained. Run anomaly_detection.py first.")
                        return

                    X = vectorizer.transform(log_df['message'])
                    log_df['anomaly'] = model.predict(X)
                    log_df['anomaly'] = log_df['anomaly'].apply(lambda x: 'anomaly' if x == -1 else 'normal')
                    log_df.to_csv('log_anomalies.csv', index=False)
                    print("Anomalies saved to log_anomalies.csv")
                    print(log_df.head())

        if args.view_baseline:
            self.monitor_changes.view_baseline()

        if args.reset_baseline:
            if args.dir is None:
                print("Please specify directories.")
                parser.print_help()
            else:
                self.monitor_changes.reset_baseline(monitored_dirs)

        if not (args.monitor or args.view_baseline or args.reset_baseline or args.view_logs or args.analyze_logs):
            parser.print_help()

        if args.view_logs:
            self.monitor_changes.view_logs()

        if args.exclude:
            self.exclude_files.append(args.monitor[0])

        if args.monitor:
            if args.dir is None:
                print("Please specify directories.")
                parser.print_help()
            else:
                for directory in monitored_dirs:
                    if not os.path.exists:
                        print(f"Creating the directory: {directory}")
                        os.mkdir(directory)
                print("Starting the Integrity Monitor.")
                try:
                    self.monitor_changes.monitor_changes(monitored_dirs, self.exclude_files)
                except KeyboardInterrupt:
                    cli.authentication.authorised_credentials()
                    for changes in self.monitor_changes.reported_changes.items():
                        self.database_operation.store_information(changes[1])
                    self.monitor_changes.reset_baseline(monitored_dirs)
                    print("\n File Integrity Monitor stopped.")
                except Exception as e:
                    print(f"Error starting monitor: {e}")


if __name__ == "__main__":
    cli = CLI()
    cli.authentication.authorised_credentials()
    cli.main()
