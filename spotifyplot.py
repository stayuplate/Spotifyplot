import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import os
import logging

# Create a logger
logging.basicConfig(filename='spotify.log', level=logging.INFO)

def load_data(filepath):
    """
    Load data from a directory containing json files.
    """
    # Check if filepath exists
    if not os.path.exists(filepath):
        logging.error("The provided filepath does not exist.")
        raise FileNotFoundError("The provided filepath does not exist.")

    # Load the data
    data = []
    for filename in os.listdir(filepath):
        if filename.endswith('.json'):
            with open(os.path.join(filepath, filename), 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Handle both list and dictionary types
                    json_line = json.loads(line)
                    if isinstance(json_line, list):
                        data.extend(json_line)
                    elif isinstance(json_line, dict):
                        data.append(json_line)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

def preprocess_data(df, excluded_artists=[]):
    """
    Preprocess the data, including excluding specific artists and podcasts, and converting time data.
    """
    # Exclude podcasts and specific artists
    if 'episode_show_name' in df.columns:
        df = df[df['episode_show_name'].isna()]
    if 'master_metadata_album_artist_name' in df.columns:
        df = df[~df['master_metadata_album_artist_name'].isin(excluded_artists)]

    # Preprocessing
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])
    if 'ms_played' in df.columns:
        df['ms_played_hours'] = df['ms_played'] / (1000*60*60)  # Convert ms to hours
        df['ms_played_minutes'] = df['ms_played_hours'] * 60  # Convert hours to minutes
    return df

def calculate_metrics(df, num_artists):
    """
    Calculate the metrics for the top artists.
    """
    if 'master_metadata_album_artist_name' in df.columns:
        top_artists = df['master_metadata_album_artist_name'].value_counts().head(num_artists)
        artist_duration = df.groupby('master_metadata_album_artist_name')['ms_played_hours'].sum()
        mean_track_duration = df.groupby('master_metadata_album_artist_name')['ms_played_minutes'].mean()
    else:
        logging.error("Artist name data not available in the provided files.")
        raise ValueError("Artist name data not available in the provided files.")

    # Create the dataframe for the plot
    df_top_artists = pd.DataFrame({'Plays': top_artists, 
                                   'Listening Hours': artist_duration.loc[top_artists.index], 
                                   'Mean Track Duration': mean_track_duration.loc[top_artists.index]})
    return df_top_artists

def create_plot(df_top_artists, plot_size=(15, 10), plot_style="whitegrid", color_palette='pastel', save_to='MyData', dpi=300):
    """
    Create the plot for the top artists.
    """
    # Create the plot
    plt.figure(figsize=plot_size)  # Increase the size of the plot
    sns.set(style=plot_style)
    colors = sns.color_palette(color_palette)[0:len(df_top_artists)]

    # Plotting total plays
    ax1 = sns.barplot(x=df_top_artists.index, y=df_top_artists['Plays'], palette=colors, alpha=0.8)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha="right", fontsize=10)  # Rotate labels and decrease font size

    # Adding secondary y-axis for other metrics
    ax2 = ax1.twinx()
    ax2 = sns.lineplot(x=df_top_artists.index, y=df_top_artists['Listening Hours'], sort=False, color='blue', label='Total Listening Hours')
    ax2 = sns.lineplot(x=df_top_artists.index, y=df_top_artists['Mean Track Duration'], sort=False, color='red', label='Mean Track Duration (Minutes)')

    # Setting labels and title
    ax1.set_xlabel('Artist', fontsize=12)
    ax1.set_ylabel('Total Plays', fontsize=12)
    ax2.set_ylabel('Value', fontsize=12)
    plt.title(f'Top {len(df_top_artists)} Artists - Spotify', fontsize=14)

    # Show the plot
    plt.tight_layout()  # Adjust subplot parameters to give specified padding

    # Save the plot to a file if save_to is provided
    if save_to is not None:
        plt.savefig(save_to, dpi=dpi)
        logging.info(f"Plot saved to {save_to}")

def top_artists(filepath, num_artists=50, excluded_artists=[]):
    """
    This function takes a filepath to the Spotify data and creates a visualization of the top most listened artists.
    """
    df = load_data(filepath)
    df = preprocess_data(df, excluded_artists)
    df_top_artists = calculate_metrics(df, num_artists)
    create_plot(df_top_artists, save_to='top_artists.png')

def main():
    top_artists('MyData', num_artists=50, excluded_artists=['Peppa Pig Hörspiele'])

if __name__ == "__main__":
    main()