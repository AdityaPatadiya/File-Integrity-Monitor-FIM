# TrustVault

The File Integrity Monitor (FIM) is a CLI tool designed to monitor directories for changes, view and reset baseline data, view logs, and analyze log files for anomalies. It includes user authentication to ensure that only authorized users can access and use the tool. Additionally, it takes a backup of the monitored directories before starting the monitoring process.

## Features

- **Monitor Directories**: Start monitoring single or multiple directories for changes.
- **View Baseline Data**: View the current baseline data.
- **Reset Baseline Data**: Reset the baseline data for specified directories.
- **View Logs**: View the log file.
- **Analyze Logs**: Analyze the log file for anomalies using machine learning.
- **Exclude Files/Folders**: Exclude selected files and folders from monitoring.
- **User Authentication**: Ensure only authorized users can access and use the tool.
- **Backup**: Take a backup of the monitored directories before starting the monitoring process.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/AdityaPatadiya/FIM.git
    cd FIM
    ```
## Usage
### Authentication
When you run the CLI tool, you will be prompted to authenticate. If you are a new user, you can register by providing a username and password. If you are an existing user, you can log in with your credentials.

### Command-Line Arguments
* `--monitor`: Start monitoring multiple directories.
* `--view-baseline`: View the current baseline data.
* `--reset-baseline`: Reset the baseline data.
* `--view-logs`: View the log file.
* `--analyze-logs`: Analyze the log file for anomalies.
* `--exclude`: Exclude selected files and folders.
* `--dir`: Add directories to monitor.

### Examples
1. Monitor Directories:
    ```sh
    python cli.py --monitor --dir /path/to/dir1 /path/to/dir2
    ```
2. View Baseline Data:
    ```sh
    python cli.py --view-baseline
    ```
3. Reset Baseline Data:
    ```sh
    python cli.py --reset-baseline --dir /path/to/dir1 /path/to/dir2
    ```
4. View Logs:
    ```sh
    python cli.py --view-logs
    ```
5. Analyze Logs:
    ```sh
    python cli.py --analyze-logs
    ```
6. Exclude Files/Folders:
    ```sh
    python cli.py --exclude /path/to/exclude
    ```

## Project Structure
* `cli.py`: Main CLI tool for the File Integrity Monitor.
* `FIM.py`: file containing the core functionality for monitoring changes.
* `fim_utils.py`: containing the core methods used in FIM.py module.
* `database.py`: Handles database operations for storing baseline data.
* `Authentication`: Directory containing the authentication module.
* `backup.py`: Script for handling backups of monitored directories.
* `log_parser.py`: Script for parsing the log file.
* `anomaly_detection.py`: Script for performing anomaly detection on the log file.
* `baseline.json`: file containing information like hashes, modified_time etc.. for monitored directory.
* `FIM_Logging.log`: file containing logs that shows the changes.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
