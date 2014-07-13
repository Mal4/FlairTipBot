import re, praw, logging, requests
from Bot import Bot, Comment, Database

db = Database()

class FlairTipBot(Bot):
    def run(self):
        while True:
            self.loop()

    # Check the latest hot submissions in subreddit
    def check_submissions(self, subreddit):
        subreddit = self.reddit.get_subreddit(subreddit)
        for submission in subreddit.get_hot(limit=30):
            submission.replace_more_comments(limit=None, threshold=0)
            comments = praw.helpers.flatten_tree(submission.comments)
            for comment in comments:
                if not Comment.is_parsed(comment.id) and comment.author:
                    self.check_triggers(comment, subreddit)
                    Comment.add(comment.id, self.db.session)
        self.idle_count += 1

    def check_messages(self):
        messages = self.reddit.get_unread()
        for message in messages:
            self.check_pm_triggers(message)
            message.mark_as_read()
        pass

    # Set certain parameters and variables for the bot
    def set_configurables(self):
        Bot.set_configurables(self)
        self.owner = self.reddit.get_redditor('FlockOnFire')
        self.currency = 'R'
        self.reply_footer = """ 
^([[help]](http://www.reddit.com/r/RedditPointTrade/))
\n___\n
^(\'Spend\' your Reddits at /r/RedditPointTrade)
        """
        self.gift_amount = 1
        self.karma_minimum = 100
        self.triggers = {
            '+accept'   : re.compile(r'\+accept', re.I), 
            '[request]' : re.compile(r'\[R\] ?\[[^\d]?(\d+)\]', re.I),
            '[offer]'   : re.compile(r'\[O\] ?\[[^\d]?(\d+)\]', re.I),
            '+reddittip': re.compile(r'\+redditpointtrade (\d+)', re.I),
            'pm_tip'    : re.compile(r'\+redditpointtrade ([a-z0-9_-]{3,}) [^\d]?(\d+)', re.I),
            'pm_join'   : re.compile(r'\+join (/r/)?([a-z0-9_-]{3,})', re.I),
            'pm_leave'  : re.compile(r'\+leave (/r/)?([a-z0-9_-]{3,})', re.I),
            'pm_balance': re.compile(r'(\+balance)', re.I)
        }
        self.sub_from_subscriptions = True
        self.home = self.reddit.get_subreddit('RedditPointTrade')
        # self.subreddits = [sub.display_name for sub in self.reddit.get_my_subreddits()]
        
        self.messages = {
            'verified'    : '\n\n^(**[Verified]** /u/{0} -> /u/{1} {2}{3}.00)',
            'accepted'    : '\n\n^(**[Verified]** /u/{0} -> /u/{1} {2}{3}.00)',
            'failed'      : '\n\n^(**[Failed]** /u/{0} -/-> /u/{1} {2}{3}.00)',
            'welcome_gift': '\n\n^(**Welcome /u/{0},**\n\n To get you started you have received {1}{2}.00!)',
            'pm_tip'      : '[RPT] Private Transaction',
            'pm_join'     : 'RedditPointTrade Bot joined your subreddit. For more info check /r/{0} or contact /u/{1}'.format(str(self.home), str(self.owner)),
            'pm_leave'    : 'RedditPointTrade Bot has left your subreddit.',
            'pm_balance'  : 'Your /r/RedditPointTrade balance is: {0}'
        }
        self.flair_css = 'balance'

    # Check comment for triggers
    def check_triggers(self, comment, subreddit):
        is_new  = self.new_user(comment.author)
        accept  = self.triggers['+accept'].search(comment.body) 
        tip     = self.triggers['+reddittip'].search(comment.body)

        reply = ''
        if is_new and subreddit == self.home:
            reply += is_new
        if accept:
            reply += self.accept(comment)
        if tip:
            reply += self.tip_user(tip.group(1), comment)

        if reply != '':    
            reply += self.reply_footer
            Bot.handle_ratelimit(comment.reply, reply)
            self.idle_count = 0

    def check_pm_triggers(self, message):
        print(message.body)
        tip   = self.triggers['pm_tip'].search(message.body)
        join  = self.triggers['pm_join'].search(message.body)
        leave = self.triggers['pm_leave'].search(message.body)
        balance = self.triggers['pm_balance'].search(message.body)

        if tip:
            reply = self.tip_user(tip.group(2), user_from = message.author, user_to = tip.group(1))
            message.reply(reply)
            self.reddit.send_message(tip.group(1), self.messages['pm_tip'], reply)
        elif balance:
            flair = self.flair_to_int(user=message.author)
            message.reply(self.messages['pm_balance'].format(str(flair)))
        elif join:
            try:
                joined_sub = self.reddit.get_subreddit(join.group(2))
                joined_sub.subscribe()
                self.reddit.send_message(joined_sub, 'Automated Message', self.messages['pm_join'])
            except:
                message.reply('We failed to join your sub.')
        elif leave:
            #try:
            left_sub = self.reddit.get_subreddit(leave.group(2))
            left_sub.unsubscribe()
            self.reddit.send_message(left_sub, 'Automated Message', self.messages['pm_leave'])
            #except:
            #    message.reply('We failed to leave your sub. I notified my owner (/u/{0}) with the problem.'.format(str(self.owner)))
            #    self.reddit.send_message(self.owner, 'Task Failure', 'Failed to leave /r/{0} on orders of /u/{1}'.format(leave.group(2), str(message.author)))

    def accept(self, comment):
        price = self.get_price(comment.submission)
        is_request = self.get_type(comment.submission) == 'request'
        if any([is_request and comment.author != comment.submission.author, not is_request and self.get_parent(comment).author != comment.submission.author]):
            return ''

        trans = self.transaction(comment.author, self.get_parent(comment).author, price)
        if trans:
            logging.info('{0} tipped {1}'.format(str(comment.author), str(self.get_parent(comment).author)))
            return self.messages['verified'].format(str(comment.author), str(self.get_parent(comment).author), self.currency, price)
        else:
            logging.info('{0} failed to tip {1}'.format(str(comment.author), str(self.get_parent(comment).author)))
            return self.messages['failed'].format(str(comment.author), str(self.get_parent(comment).author), self.currency, price)

    def tip_user(self, amount, comment=None, user_from=None, user_to=None):
        amount = int(amount)
        if comment:
            user_from = comment.author
            user_to   = self.get_parent(comment).author
        try:
            trans = self.transaction(user_from, user_to, amount)
        except:
            trans = False
        if trans:
            logging.info('{0} tipped {1}'.format(str(user_from), user_to))
            return self.messages['verified'].format(str(user_from), user_to, self.currency, amount)
        else:
            logging.info('{0} failed to tip {1}'.format(str(user_from), user_to))
            return self.messages['failed'].format(str(user_from), user_to, self.currency, amount)

    def new_user(self, user):
        if user.link_karma + user.comment_karma < 100:
            return None
        flair = self.reddit.get_flair(self.home, user)
        if not flair or flair['flair_text'] == '':
            self.flair_user(user, self.gift_amount)
            logging.info('New user: {0}'.format(str(user)))
            return self.messages['welcome_gift'].format(str(user), self.currency, self.gift_amount)
        else:
            return None

    def transaction(self, user_from, user_to, amount):
        debtor = {
            'name':    str(user_from),
            'balance': self.flair_to_int(user=user_from)
        }
        creditor = {
            'name':    str(user_to),
            'balance': self.flair_to_int(user=user_to)
        }
        if debtor['balance'] > amount:
            self.flair_user(user_from, debtor['balance'] - amount)
            self.flair_user(user_to, creditor['balance'] + amount)
            logging.info('Transaction ({0}): {1}[{2}] -> {3}[{4}]'.format(
                amount,
                debtor['name'], debtor['balance'],
                creditor['name'], creditor['balance']
            ))
            return True
        return False

    def flair_to_int(self, flair_text=None, user=None):
        if user:
            flair = self.reddit.get_flair(self.home, user)
            if flair and flair['flair_text']:
                flair_text = flair['flair_text']
            else:
                flair_text = '0'
        flair_num = flair_text.replace(',', '')
        return int(flair_num)

    def int_to_flair(self, num):
        return '{:,}'.format(num)

    def flair_user(self, user, amount):
        self.home.set_flair(str(user), self.int_to_flair(amount), self.flair_css)

    def get_price(self, submission=None, match=None):
        if match:
            return match.group(1)
        else:
            request = self.triggers['[request]'].search(submission.title)
            offer = self.triggers['[offer]'].search(submission.title)
            if request:
                return int(request.group(1))
            elif offer:
                return int(offer.group(1))
            return None

    def get_type(self, submission):
        request = self.triggers['[request]'].search(submission.title)
        offer = self.triggers['[offer]'].search(submission.title)
        if request:
            return 'request'
        elif offer:
            return 'offer'
        else:
            return None

    def get_parent(self, comment):
        return self.reddit.get_info(thing_id=comment.parent_id)

bot = FlairTipBot('Point Trade Tip Bot by /u/FlockOnFire and /u/malz_', 'bot.log', from_file='login.cred', database=db)
bot.run()