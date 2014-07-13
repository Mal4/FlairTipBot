# Flair Tip Bot
Flair Tip Bot is a bot that saves the balance of a user in the flair of the specified subreddit.

            '+accept'   : re.compile(r'\+accept', re.I), 
            '[request]' : re.compile(r'\[R\] ?\[[^\d]?(\d+)\]', re.I),
            '[offer]'   : re.compile(r'\[O\] ?\[[^\d]?(\d+)\]', re.I),
            '+reddittip': re.compile(r'\+redditpointtrade (\d+)', re.I),
            'pm_tip'    : re.compile(r'\+redditpointtrade ([a-z0-9_-]{3,}) [^\d]?(\d+)', re.I),
            'pm_join'   : re.compile(r'\+join (/r/)?([a-z0-9_-]{3,})', re.I),
            'pm_leave'  : re.compile(r'\+leave (/r/)?([a-z0-9_-]{3,})', re.I),
            'pm_balance': re.compile(r'(\+balance)', re.I)

## Commands
Below are the commands the Flair Tip Bot understands.

### Accept offer
> +accept

Accepts the solution of the user to which the requester replied.
The user receives the point specified in the title of the submission for his solution. 

### Tip User
> +redditpointtrade 123

Tips the user to which the tipper replied with 123 points.

## PM Commands

Flair Tip Bot can join and leave subreddits, check your balance or privately tip users.

### Check Balance
> +balance

The bot replies to your PM with your current balance.

### Join Subreddit
> +join my_subreddit

Subscribes the bot to /r/my_subreddit. After subscribing the bot check the comments for the above comment commands in that subreddit.
The balance is still saved in the originally specified subreddit.

### Leave Subreddit
> +leave my_subreddit

Unsubscribes the bot from /r/my_subreddit. The bot no longer replies to commands in /r/my_subreddit.

### Tip User via PM
> +redditpointtrade my_friend 123

Tips /u/my_friend 123 points. Both the tipper and receiver are notified of the status of the transaction.