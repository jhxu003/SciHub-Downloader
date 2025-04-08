# SciHub-Downloader

A Python tool for batch downloading academic papers from Sci-Hub using DOIs from Excel files.

## Features

- Batch download papers from Sci-Hub using DOIs
- Support for multiple Sci-Hub mirrors
- Progress tracking with tqdm
- Automatic retry with different mirrors
- Smart filename sanitization
- Skip already downloaded files
- Detailed download statistics
- Error handling and reporting

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/SciHub-Downloader.git
cd SciHub-Downloader
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your Excel file with a 'DOI' column containing the DOIs you want to download
2. Run the script:
```bash
python scihub_downloader.py --input your_file.xlsx --output pdf_directory
```

### Command Line Arguments

- `--input`: Path to the input Excel file (required)
- `--output`: Directory to save downloaded PDFs (optional, defaults to './pdf')
- `--delay`: Delay between downloads in seconds (optional, defaults to 5)

## Example

```bash
python scihub_downloader.py --input PD1-paper.xlsx --output ./papers --delay 3
```

## Output

The script will:
1. Create the specified output directory
2. Show a progress bar with download statistics
3. Save PDFs with sanitized filenames
4. Display a summary of successful/failed downloads

## Requirements

- Python 3.8+
- pandas
- requests
- beautifulsoup4
- tqdm

## Notes

- This tool is for educational purposes only
- Please respect copyright laws and use responsibly
- The script includes delays between requests to avoid overwhelming servers
- Multiple Sci-Hub mirrors are used for reliability

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 