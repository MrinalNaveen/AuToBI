# AuToBI Prosodic Feature Extraction and Analysis Pipeline

This repository provides a detailed and automated pipeline for processing TextGrid files and WAV audio using the `autobi_py` library, a Python interface to the AuToBI (Automatic ToBI annotation) system. It converts input TextGrid annotations into an AuToBI-compatible format, runs multiple prosodic analyses, and exports the results into a CSV format.

## 📦 Features

- Converts manually annotated TextGrids into a format required by AuToBI.
- Supports six key prosodic feature extractions:
  - Pitch Accent Detection
  - Pitch Accent Classification
  - Intonational Phrase Boundary Detection
  - Intermediate Phrase Boundary Detection
  - Phrase Accent Classification
  - Boundary Tone Classification
- Outputs a DataFrame with word-level annotations and feature values.
- Saves results as CSV for downstream analysis.

---

## 🛠 Requirements

Install the following Python libraries before running the script:

```bash
pip install pandas autobi_py
```

Additionally, make sure you have Java installed and properly configured (AuToBI requires JVM).

---

## 📂 Input

- **WAV file**: Raw audio file (e.g., `1677.wav`)
- **TextGrid file**: Annotation file containing at least a `words` tier (e.g., `1677.TextGrid`)

---

## 🚀 How to Run

### Step 1: Prepare Your Environment

Ensure your WAV and TextGrid files are located in the expected directory (or update the paths in `main()` accordingly).

### Step 2: Run the Script

Simply execute:

```bash
python script_name.py
```

Replace `script_name.py` with the name of your Python file.

### Step 3: Output

The output CSV will be saved in:

```
C:/Users/Dell/EG/autobi_py-1/Testing/expert/output/1677.csv
```

This CSV contains word-level annotations with extracted prosodic features.

---

## 📊 Output Fields

The final CSV will include:

| Column | Description |
|--------|-------------|
| `word` | The actual word label from the TextGrid |
| `start_time` | Start time of the word |
| `end_time` | End time of the word |
| `PitchAccent` | Whether the word is pitch-accented (YES/NO) |
| `PitchAccentType` | Type of pitch accent (e.g., H*, L+H*, !H*) |
| `IntonationalPhraseBoundary` | Binary value indicating phrase boundary |
| `IntermediatePhraseBoundary` | Binary value indicating intermediate boundary |
| `PhraseAccent` | Phrase accent label (e.g., H-, L-) |
| `BoundaryTone` | Boundary tone label (e.g., H%, L%) |

---

## 🧠 Key Components Explained

### `convert_textgrid_for_autobi()`

- Converts a standard TextGrid to a format required by AuToBI, with specific tiers: `tones`, `words`, `breaks`, and `misc`.

### `extract_words_from_textgrid()`

- Parses the `words` tier and extracts timings and labels of spoken words (excluding silences).

### `analyze_prosody()`

- Core function that runs all six AuToBI feature extractors and maps results to word-level data.
- Uses `AutobiJVMHandler` to manage JVM.
- Applies cleaning and formatting to output columns.

### `clean_column_name()`

- Standardizes column names to avoid issues when using pandas.

---

## 🐞 Troubleshooting

- If you receive `FileNotFoundError`, double-check the paths to your input files.
- If the CSV is not saved, make sure the output directory exists and you have write permissions.
- Ensure Java is correctly installed and accessible via your system PATH.

---

## 📌 Notes

- This script is tightly coupled with the structure of AuToBI and expects the Java environment to be ready.
- Designed for batch or single-file analysis of high-quality annotated speech.

---

## 📁 File Structure (Example)

```
your-project/
├── script.py
├── expert/
│   ├── 1677.wav
│   ├── 1677.TextGrid
│   └── output/
│       └── 1677.csv
```


## 📄 License

MIT License or based on usage terms of AuToBI.

---
