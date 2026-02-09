
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_movie_data(num_rows=1000):
    """Generates a synthetic movie dataset for testing."""
    
    genres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance', 'Documentary']
    directors = ['Christopher Nolan', 'Steven Spielberg', 'Martin Scorsese', 'Quentin Tarantino', 'Greta Gerwig', 'James Cameron', 'Unknown Director']
    studios = ['Warner Bros', 'Universal', 'Paramount', 'Disney', 'Sony', 'Indie']
    
    data = []
    
    # Start date for random date generation
    start_date = datetime(2000, 1, 1)
    
    for i in range(num_rows):
        # Generate random date
        random_days = random.randint(0, 365 * 24)
        date = start_date + timedelta(days=random_days)
        
        # introduce mixed date formats for testing robustness
        if i % 10 == 0:
            date_str = date.strftime('%d-%m-%Y') # DD-MM-YYYY (The tricky one)
        elif i % 15 == 0:
            date_str = date.strftime('%Y/%m/%d')
        else:
            date_str = date.strftime('%Y-%m-%d')
            
        # Core metrics
        budget = random.randint(1, 300) * 1000000
        # Revenue correlated with budget but with variance
        revenue = budget * random.uniform(0.5, 5.0) if random.random() > 0.1 else 0 # 10% flops with 0 revenue
        
        row = {
            'Movie_ID': f"MV-{i:05d}",
            'Title': f"Movie Title {i}",
            'Genre': random.choice(genres),
            'Release_Date': date_str,
            'Budget_USD': budget,
            'Revenue_USD': int(revenue),
            'Director': random.choice(directors),
            'Studio': random.choice(studios),
            'Runtime_Minutes': random.randint(80, 180),
            'IMDB_Rating': round(random.uniform(1.0, 10.0), 1),
            'Votes': random.randint(100, 100000)
        }
        
        data.append(row)
        
    df = pd.DataFrame(data)
    
    # Introduce some missing values for profiling test
    df.loc[df.sample(frac=0.05).index, 'Budget_USD'] = np.nan
    df.loc[df.sample(frac=0.02).index, 'Director'] = None
    
    return df

if __name__ == "__main__":
    from pathlib import Path
    
    # Create data directory if it doesn't exist
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    df = generate_movie_data(500)
    output_path = output_dir / "movie_test_data.csv"
    
    df.to_csv(output_path, index=False)
    print(f"Generated test dataset at: {output_path}")
    print(df.head())
