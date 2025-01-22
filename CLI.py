import os
import argparse
from FIM import monitor_changes


class CLI:
    def __init__(self):
        self.monitor_changes = monitor_changes()
        self.exclude_files = []

    def main(self):
        parser = argparse.ArgumentParser(description="File Integrity Monitor CLI Tool")
        parser.add_argument("--monitor", action="store_true", help="Start monitoring multiple directory")
        parser.add_argument("--view-baseline", action="store_true", help="View the current baseline data")
        parser.add_argument("--reset-baseline", action="store_true", help="Reset the baseline data")
        parser.add_argument("--view-logs", action="store_true", help="View the log file")
        parser.add_argument("--exclude", type=str, help="Exclude selected file and folder")
        parser.add_argument("--dir", nargs="+", type=str, help="Add directories to monitor.")

        args = parser.parse_args()
        if args.dir is not None:
            monitored_dirs = [os.path.abspath(dir) for dir in args.dir]

        if args.view_baseline:
            self.monitor_changes.view_baseline()
        if args.reset_baseline:
            if args.dir is None:
                print("Please specify directories.")
                parser.print_help()
            else:
                self.monitor_changes.reset_baseline(monitored_dirs)
        if not (args.monitor or args.view_baseline or args.reset_baseline or args.view_logs):
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
                    print("\n File Integrity Monitor stopped.")


if __name__ == "__main__":
    cli = CLI()
    cli.main()
