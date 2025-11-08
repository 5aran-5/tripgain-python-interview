import pandas as pd

df = pd.read_csv("matches.csv")



#Q1
print("Total number of matches:", len(df))
print("Column names:", df.columns.tolist())
print("First 5 rows of Data:\n", df.head())
print("Description of Data:\n", df.describe(include='all'))

#Q2
matches = df[(df['win_by_runs'] == 1) | (df['win_by_wickets'] == 1)]
top_player = matches['player_of_match'].value_counts()
print("\nPlayer with most Player of the Match awards:", top_player)

# Q3
wankhede_df = df[df['venue'].str.contains("Wankhede", case=False, na=False)]
first = wankhede_df[wankhede_df['win_by_runs'] > 0].shape[0]
second = wankhede_df[wankhede_df['win_by_wickets'] > 0].shape[0]
print("\nBatting first wins:", first, ", Batting second wins:", second)
if (first > second):
    print("At Wankhede Stadium,it is more common to win by batting first (runs)")
else: 
    print("At Wankhede Stadium,it is more common to win by batting second (wicket) ")
    
    
# Q4
team = df[df['win_by_runs'] > 50]['winner'].value_counts().idxmax()
print("\nTeam with highest wins where victory margin was greater than 50 runs:", team)


# Q5
win = df[(df['toss_winner'] == df['winner']) & (df['toss_decision'] == 'bat')].shape[0]
print("\nTimes team that won the toss also set a target and won the match :", win)

# Q6
kkr_matches = df[(df['team1'] == 'Kolkata Knight Riders') | (df['team2'] == 'Kolkata Knight Riders')]
umpire1 = kkr_matches['umpire1'].value_counts().idxmax()
umpire2 = kkr_matches['umpire2'].value_counts().idxmax()
if kkr_matches['umpire1'].value_counts().max() >= kkr_matches['umpire2'].value_counts().max() : 
    most = umpire1     
else :
    most = umpire2
print("\nUmpire who officiated more KKR matches:", most)