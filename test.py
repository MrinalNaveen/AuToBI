import logging
from pathlib import Path
import pandas as pd
import re

from autobi.core import AutobiJVMHandler
from autobi import ArgumentBuilder, DatasetBuilder, FeaturenamesBuilder

# Configure logging to suppress warnings
logging.getLogger('py4j').setLevel(logging.ERROR)
logging.getLogger('log4j').setLevel(logging.ERROR)

def convert_textgrid_for_autobi(input_textgrid: Path, output_textgrid: Path) -> bool:
    """Convert TextGrid file to format expected by AuToBI"""
    try:
        with open(input_textgrid, 'r') as f:
            content = f.read()
            
        # Extract the words tier
        words_section = re.search(r'name = "words".*?intervals: size = (\d+)', content, re.DOTALL)
        if not words_section:
            print("Could not find words tier in TextGrid file")
            return False
            
        # Create a new TextGrid file with all required tiers
        new_content = f'''File type = "ooTextFile"
Object class = "TextGrid"

xmin = 0
xmax = 2.38
tiers? <exists>
size = 4
item []:
    item [1]:
        class = "TextTier"
        name = "tones"
        xmin = 0
        xmax = 2.38
        points: size = 0
    item [2]:
        class = "IntervalTier"
        name = "words"
        xmin = 0
        xmax = 2.38
        intervals: size = {words_section.group(1)}
'''
        
        # Add the intervals
        intervals = re.findall(r'intervals \[\d+\]:\s+xmin = ([\d.]+)\s+xmax = ([\d.]+)\s+text = "([^"]*)"', content)
        for i, (start, end, text) in enumerate(intervals, 1):
            if text.strip() and text != "#":  # Skip silence markers
                new_content += f'''        intervals [{i}]:
            xmin = {start}
            xmax = {end}
            text = "{text}"
'''
        
        # Add breaks tier
        new_content += '''    item [3]:
        class = "TextTier"
        name = "breaks"
        xmin = 0
        xmax = 2.38
        points: size = 0
    item [4]:
        class = "TextTier"
        name = "misc"
        xmin = 0
        xmax = 2.38
        points: size = 0
'''
        
        # Write the new TextGrid file
        with open(output_textgrid, 'w') as f:
            f.write(new_content)
            
        print(f"Created AuToBI-compatible TextGrid file: {output_textgrid}")
        return True
        
    except Exception as e:
        print(f"Error creating AuToBI TextGrid file: {str(e)}")
        return False

def extract_words_from_textgrid(textgrid_path: Path) -> list[dict]:
    """Extract words and timing from TextGrid file"""
    try:
        with open(textgrid_path, 'r') as f:
            content = f.read()
            
        # Find words tier
        words_section = re.search(r'name = "words".*?intervals: size = (\d+)', content, re.DOTALL)
        if not words_section:
            print("Could not find words tier in TextGrid file")
            return []
            
        # Extract intervals
        intervals = re.findall(r'intervals \[\d+\]:\s+xmin = ([\d.]+)\s+xmax = ([\d.]+)\s+text = "([^"]*)"', content)
        words = []
        
        for start, end, text in intervals:
            if text.strip() and text != "#":  # Skip silence markers
                words.append({
                    'word': text,
                    'start_time': float(start),
                    'end_time': float(end)
                })
                
        print(f"Successfully extracted {len(words)} words from TextGrid")
        return words
        
    except Exception as e:
        print(f"Error reading TextGrid file: {str(e)}")
        return []

def clean_column_name(name: str) -> str:
    """Clean column names for pandas DataFrame"""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    return 'F_' + cleaned if not cleaned[0].isalpha() else cleaned

def analyze_prosody(wav_path: Path, textgrid_path: Path) -> pd.DataFrame:
    """Analyze prosody using AuToBI"""
    # Verify input files
    if not wav_path.exists() or not textgrid_path.exists():
        raise FileNotFoundError("Input files not found")
        
    print(f"\nProcessing files:")
    print(f"WAV: {wav_path}")
    print(f"TextGrid: {textgrid_path}")
    
    # Convert TextGrid to AuToBI format
    output_textgrid = textgrid_path.parent / "autobi_input.TextGrid"
    if not convert_textgrid_for_autobi(textgrid_path, output_textgrid):
        raise ValueError("Failed to create AuToBI-compatible TextGrid file")
    
    # Extract words first
    words = extract_words_from_textgrid(textgrid_path)
    print(f"[DEBUG] Number of words extracted: {len(words)}")
    if not words:
        raise ValueError("No words found in TextGrid file")
        
    # Define feature sets to analyze
    feature_sets = {
        "Pitch Accent Detection": "PitchAccentDetectionFeatureSet",
        "Pitch Accent Classification": "PitchAccentClassificationFeatureSet",
        "Intonational Phrase Boundary Detection": "IntonationalPhraseBoundaryDetectionFeatureSet",
        "Intermediate Phrase Boundary Detection": "IntermediatePhraseBoundaryDetectionFeatureSet",
        "Phrase Accent Classification": "PhraseAccentClassificationFeatureSet",
        "Boundary Tone Classification": "PhraseAccentBoundaryToneClassificationFeatureSet"
    }
    
    # Initialize results DataFrame
    results_df = pd.DataFrame(words)
    print(f"[DEBUG] Initial results_df shape: {results_df.shape}")
    print(f"[DEBUG] Initial results_df indices: {results_df.index.tolist()}")
    print(f"[DEBUG] Initial results_df sample:\n{results_df.head(10)}")
    
    # Process each feature set
    with AutobiJVMHandler() as jvm:
        # Set up base arguments
        argument_builder = ArgumentBuilder(jvm)
        argument_builder.with_input_wav(wav_path)
        argument_builder.with_input_TextGrid(output_textgrid)
        
        # Enable all classifiers
        argument_builder.with_pitch_accent_detector(Path("default"))
        argument_builder.with_pitch_accent_classifier(Path("default"))
        argument_builder.with_intonal_phrase_boundary_detector(Path("default"))
        argument_builder.with_intermediate_phrase_boundary_detector(Path("default"))
        argument_builder.with_phrase_accent_classifier(Path("default"))
        
        args = argument_builder.to_args_string()
        
        for analysis_name, feature_set_name in feature_sets.items():
            try:
                print(f"\nProcessing {analysis_name}...")
                
                # Create feature set
                builder = FeaturenamesBuilder(jvm)
                builder.with_default_features(feature_set_name)
                featureset = builder.build()
                
                # Extract features
                databuilder = DatasetBuilder(jvm, args)
                databuilder.with_feature_set(featureset)
                features_df = databuilder.build_pandas()
                print(f"\n[DEBUG] AuToBI extracted features for {analysis_name}:")
                print(f"Number of features: {len(features_df.columns)}")
                print("Feature names:", features_df.columns.tolist())
                print("\nSample of raw feature values:")
                print(features_df.head())
                
                if features_df.empty:
                    print(f"Warning: No features extracted for {analysis_name}")
                    continue
                    
                # Clean column names
                features_df.columns = [clean_column_name(col) for col in features_df.columns]
                print(f"Available columns for {analysis_name}: {features_df.columns.tolist()}")
                
                # Add results to main DataFrame
                if analysis_name == "Pitch Accent Detection":
                    pitch_cols = [col for col in features_df.columns if any(x in col.lower() for x in ['pitch_accent', 'f0', 'log_f0'])]
                    if pitch_cols:
                        results_df['PitchAccent'] = features_df[pitch_cols[0]].apply(lambda x: 'YES' if x > 0.5 else 'NO')
                        
                elif analysis_name == "Pitch Accent Classification":
                    type_cols = [col for col in features_df.columns if any(x in col.lower() for x in ['f0', 'log_f0', 'pitch'])]
                    if type_cols:
                        results_df['PitchAccentType'] = features_df[type_cols[0]].apply(lambda x: 'H*' if x > 0.5 else 'L+H*' if x < -0.5 else '!H*')
                        
                elif analysis_name == "Intonational Phrase Boundary Detection":
                    boundary_cols = [col for col in features_df.columns if any(x in col.lower() for x in 
                        ['boundary', 'pause', 'silence', 'duration', 'f0', 'energy', 'ip'])]
                    if boundary_cols:
                        print(f"Found boundary columns: {boundary_cols}")
                        # Convert to binary values
                        results_df['IntonationalPhraseBoundary'] = features_df[boundary_cols[0]].apply(
                            lambda x: 1 if x > 0 else 0)
                    else:
                        print("No boundary-related columns found")
                        
                elif analysis_name == "Intermediate Phrase Boundary Detection":
                    ip_boundary_cols = [col for col in features_df.columns if any(x in col.lower() for x in 
                        ['boundary', 'pause', 'silence', 'duration', 'f0', 'energy', 'ip'])]
                    if ip_boundary_cols:
                        print(f"Found intermediate boundary columns: {ip_boundary_cols}")
                        # Convert to binary values
                        results_df['IntermediatePhraseBoundary'] = features_df[ip_boundary_cols[0]].apply(
                            lambda x: 1 if x > 0 else 0)
                    else:
                        print("No intermediate boundary-related columns found")
                        
                elif analysis_name == "Phrase Accent Classification":
                    accent_cols = [col for col in features_df.columns if any(x in col.lower() for x in 
                        ['accent', 'f0', 'log_f0', 'pitch', 'energy', 'duration'])]
                    if accent_cols:
                        print(f"\nFound accent columns: {accent_cols}")
                        print("\nSample of feature values:")
                        print(features_df[accent_cols].head())
                        
                        # Use classifier output directly
                        results_df['PhraseAccent'] = features_df[accent_cols[0]].apply(
                            lambda x: 'H-' if x > 0 else 'L-' if x < 0 else '')
                        print("\nFinal phrase accent labels:")
                        print(results_df[['word', 'PhraseAccent']].head())
                    else:
                        print("No accent-related columns found")
                        
                elif analysis_name == "Boundary Tone Classification":
                    boundary_tone_cols = [col for col in features_df.columns if any(x in col.lower() for x in 
                        ['boundary', 'tone', 'f0', 'log_f0', 'pitch', 'energy', 'duration'])]
                    if boundary_tone_cols:
                        print(f"\nFound boundary tone columns: {boundary_tone_cols}")
                        print("\nSample of feature values:")
                        print(features_df[boundary_tone_cols].head())
                        
                        # Use classifier output directly
                        results_df['BoundaryTone'] = features_df[boundary_tone_cols[0]].apply(
                            lambda x: 'H%' if x > 0 else 'L%' if x < 0 else '')
                        print("\nFinal boundary tone labels:")
                        print(results_df[['word', 'BoundaryTone']].head())
                    else:
                        print("No boundary tone-related columns found")
                
                print(f"Successfully processed {analysis_name}")
                print(f"[DEBUG] results_df shape after {analysis_name}: {results_df.shape}")
                print(f"[DEBUG] results_df indices after {analysis_name}: {results_df.index.tolist()}")
                print(f"[DEBUG] results_df sample after {analysis_name}:\n{results_df.head(10)}")
                
            except Exception as e:
                print(f"Error processing {analysis_name}: {str(e)}")
                continue
    
    # Clean up the temporary TextGrid file
    try:
        output_textgrid.unlink()
    except:
        pass
        
    return results_df

def main():
    # Input files
    input_wav = Path("C:/Users/Dell/EG/autobi_py-1/Testing/expert/1677.wav")
    input_grid = Path("C:/Users/Dell/EG/autobi_py-1/Testing/expert/1677.TextGrid")
    
    try:
        # Run analysis
        results = analyze_prosody(input_wav, input_grid)
        
        if not results.empty:
            # Save results in the prosodic_analysis subdirectory
            output_dir = Path("C:/Users/Dell/EG/autobi_py-1/Testing/expert/output")
            output_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
            
            output_file = output_dir / "1677.csv"
            
            try:
                results.to_csv(output_file, index=False)
                print(f"\nAnalysis saved to: {output_file}")
                print(f"Results shape: {results.shape}")
                print("\nSample of results:")
                print(results.head())
            except PermissionError:
                print(f"\nError: Could not save to {output_file}")
                print("Please ensure you have write permissions for this directory.")
        else:
            print("\nNo results were generated")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main()