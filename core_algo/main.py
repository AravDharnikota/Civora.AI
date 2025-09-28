#!/usr/bin/env python3
"""
Main algorithm module for Civora
"""

import sys
import os

# Add the Scripts directory to the path to import the clustering function
sys.path.append('/Users/arav/Documents/Civora/Scripts/article_sim_trials/iter_4')

# Import the module (note the dot in the filename)
import importlib.util
spec = importlib.util.spec_from_file_location("iter_4_0", "/Users/arav/Documents/Civora/Scripts/article_sim_trials/iter_4/iter_4.0.py")
iter_4_0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iter_4_0)

# Import the functions
cluster_articles = iter_4_0.cluster_articles
print_groups = iter_4_0.print_groups

def main():
    """Main function to run the article clustering algorithm"""
    
    # Define file paths
    articles_file = '/Users/arav/Documents/Civora/Scripts/article_sim_trials/iter_4/articles.txt'
    system_prompt_file = '/Users/arav/Documents/Civora/Scripts/article_sim_trials/iter_2/system_prompt.txt'
    
    # Cluster articles with default threshold of 0.7
    print("Starting article clustering...")
    groups = cluster_articles(articles_file, system_prompt_file, threshold=0.7)
    
    # Print the results
    print_groups(groups)
    
    print(f"\nClustering complete! Found {len(groups)} groups.")
    
    return groups

if __name__ == "__main__":
    main()
