from src.pipeline import run_pipeline

# Test with sample
result = run_pipeline("data/raw/combined.txt", "test_source")
print(result)