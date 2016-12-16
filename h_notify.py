import requests, json, traceback, sys, smtplib, email, time, datetime, pytz
from hypothesis import Hypothesis, HypothesisAnnotation
from operator import itemgetter
from email.mime.text import MIMEText
import dateutil.parser

try:
    import cPickle as pickle
except:
    import pickle 
try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode       

class Notifier(object):
    def __init__(self, type=None, token=None, pickle=None):
        self.token = token
        self.pickle = pickle + '.pickle'
        self.type = type
        assert ( self.type == 'dict' or self.type == 'set' )
        
    def save(self, obj):
        f = open(self.pickle, 'wb')
        pickle.dump(obj, f)
        f.close()

    def load(self):
        f = open(self.pickle, 'rb')
        obj = pickle.load(f)
        f.close()
        return obj
                
    def data(self):
        obj = None
        if self.type == 'set':       # e.g. ( 'annotation_id_1', 'annotation_id_2' )
            try:
                obj = self.load()
            except:
                obj = set()
            return obj
        elif self.type == 'dict':    # e.g. { 'judell' : ('annotation_id_1', 'annotation_id_2' )  }
            try:
                obj = self.load()
            except:
                obj = {}
        return obj

    def make_vars(self, anno, groupname):
        anno_url = "https://hyp.is/%s" % anno.id
        quote = anno.exact if anno.exact is not None else ''
        type = 'annotation'
        ref = None
        if len(anno.references):
            ref = anno.references[0]
            anno_url = "https://hyp.is/%s" % ref
            type = 'reply'
        tags = ', '.join(anno.tags)
        ingroup = ''
        if anno.group != '__world__':
            ingroup = 'in group %s' % groupname
        viewer = 'http://jonudell.net/h/facet.html?facet=user&search=' + anno.user # replace with Activity Pages when it's ready!
        return {
            'anno_url' : anno_url,
            'quote' : quote,
            'tags' : tags,
            'ref' : ref,
            'type' : type,
            'viewer' : viewer,
            'ingroup' : ingroup
            }

    def notify_facet(self, facet=None, value=None, groupname=None):
        params = {'_separate_replies':'true'}
        params[facet] = value
        h_url = Hypothesis().query_url.format(query=urlencode(params))
        r = None
        if self.token is not None:
            h = Hypothesis(token=self.token)
            r = h.token_authenticated_query(h_url)
        else:
            r = requests.get(h_url).json()
        rows = r['rows']
        rows += r['replies']
        cache = self.data()
        rows.sort(key=itemgetter('updated'))
        for row in rows:
            new = False
            anno = HypothesisAnnotation(row)
            if self.type == 'set':
                if anno.id not in cache:
                    cache.add(anno.id)
                    new = True
            if self.type == 'dict':
                if not value in cache:
                    cache[value] = set()
                if anno.id not in cache[value]:
                    cache[value].add(anno.id) 
                    new = True
            if new:
                self.notify(anno, groupname=groupname)
        self.save(cache)

class SlackNotifier(Notifier):
    def __init__(self, type=None, token=None, pickle=None, channel=None, hook=None):
        super(SlackNotifier, self).__init__(type=type, token=token, pickle=pickle)
        self.channel = channel
        self.hook = hook
    
    def make_simple_payload(self, text):
       return {"channel": "#" + self.channel, 
               "username": "notifier", 
               "icon_emoji": ":mailbox:",
               "text": text
              }

    def notify(self, anno=None, groupname=None):
        try:
            vars = self.make_vars(anno, groupname)
            template = '<%s|%s> added by <%s|%s> to <%s|%s> %s\n>%s\n%s\n%s__________\n'
            tags = vars['tags']
            if tags != '':
                tags = '*' + tags + '*\n'
            payload = self.make_simple_payload(template % (vars['anno_url'], vars['type'], vars['viewer'], anno.user, anno.uri, anno.doc_title, vars['ingroup'], vars['quote'], anno.text, tags) )
            print (json.dumps(payload))
            #r = requests.post(self.hook, data = json.dumps(payload))
            #print ( r.status_code )
        except:
            print ( anno.uri, anno.id, anno.user )
            print ( traceback.print_exc() )

class EmailNotifier(Notifier):
    def __init__(self, type=None, token=None, pickle=None, smtp=None, sender=None, sender_password=None, recipient=None):
        super(EmailNotifier, self).__init__(type=type, token=token, pickle=pickle)
        self.smtp = smtp
        self.sender = sender
        self.sender_password = sender_password
        self.recipient = recipient
        self.server = smtplib.SMTP('%s:587' % self.smtp)
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.sender, self.sender_password)

    def make_email_msg(self, text):
        msg = MIMEText(text, 'plain', 'utf-8')
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = 'New annotation'
        return msg

    def notify(self, anno=None, groupname=None):
        try:
            vars = self.make_vars(anno, groupname)
            template = 'Annotation (%s) added by %s to %s (%s)\n\nQuote: %s\n\nText: %s\n\n%s\n\nTags: %s'
            payload = template % ( vars['anno_url'], anno.user, anno.uri, anno.doc_title, vars['ingroup'], vars['quote'], anno.text, vars['tags'] )
            print anno.user, anno.uri
            message = self.make_email_msg(payload)
            self.server.sendmail(self.sender, [self.recipient], message.as_string())
        except:
            print ( anno.uri, anno.id, anno.user )
            print ( traceback.print_exc() )

class RssNotifier(Notifier):
    def __init__(self, type=None, token=None, pickle=None):
        super(RssNotifier, self).__init__(type=type, token=token, pickle=pickle)

    def notify(self, anno=None, groupname=None):
        try:
            data = self.data()
            data.add(anno)
            self.save(data)
        except:
            print ( anno.uri, anno.id, anno.user )
            print ( traceback.print_exc() )

    def emit_group_rss(self, group=None, groupname=None):
        from feedgen.feed import FeedGenerator
        fg = FeedGenerator()
        fg.id('https://h.jonudell.info')
        fg.title('Hypothesis group %s (%s)' % (group, groupname))
        fg.author( {'name':'Jon Udell','email':'judell@hypothes.is'} )
        fg.description("Hypothesis notifications for group %s" % groupname)
        fg.link( href='https://h.jonudell.info/group_rss' )
        fg.language('en')
        h = Hypothesis(token=self.token, limit=20)
        ids = self.data()
        annos = []
        for id in ids:
            try:
                anno = h.get_annotation(id)
                assert ('id' in anno.keys())
                annos.append(anno)
            except:
                print ( 'cannot get %s, deleted?' % id)
            annos.sort(key=itemgetter('updated'), reverse=True)
        annos = [HypothesisAnnotation(a) for a in annos]
        for anno in annos:
            fe = fg.add_entry()
            fe.id(anno.id)
            fe.title('%s %s' % (anno.user, anno.updated))
            fe.author({"email":None,"name":anno.user,"uri":None})
            dl = "https://hyp.is/%s" % anno.id
            fe.link ({"href":"%s" % dl})
            #fe.content()
            tags = ''
            if len(anno.tags):
                tags += '\n\nTags: ' + ', '.join(anno.tags)
            fe.description('url: %s\n\ndirect link %s\n\n%s\n\n%s' % ( anno.uri, dl, anno.text, tags))
            dt = dateutil.parser.parse(anno.updated)
            dt_tz = dt.replace(tzinfo=pytz.UTC)
            fe.pubdate(dt_tz)

        rssfeed  = fg.rss_str(pretty=True) # Get the RSS feed as string
        fg.rss_file('%s.xml' % group) # Write the RSS feed to a file
      

# Email recipes

def notify_email_user_activity(user=None, token=None, pickle=None, smtp=None, sender=None, sender_password=None, recipient=None):
    print ('checking user %s for recipient %s' % ( user, recipient) )
    notifier = EmailNotifier(type='dict', token=token, pickle=pickle, smtp=smtp, sender=sender, sender_password=sender_password, recipient=recipient)
    notifier.notify_facet(facet='user', value=user)

def notify_email_tag_activity(tag=None, token=None, pickle=None, smtp=None, sender=None, sender_password=None, recipient=None):
    print ('checking tag %s for recipient %s' % ( tag, recipient) )
    notifier = EmailNotifier(type='set', token=token, pickle=pickle, smtp=smtp, sender=sender, sender_password=sender_password, recipient=recipient)
    notifier.notify_facet(facet='tag', value=tag)

def notify_email_group_activity(group=None, groupname=None, token=None, pickle=None, smtp=None, sender=None, sender_password=None, recipient=None ):
    print ('checking group %s for recipient %s' % ( groupname, recipient ) )
    notifier = EmailNotifier(type='set', token=token, pickle=pickle, smtp=smtp, sender=sender, sender_password=sender_password, recipient=recipient)
    notifier.notify_facet(facet='group', value=group, groupname=groupname)

# Slack recipes

""" Watch for annotations on a set of URLs """
def notify_slack_url_activity(url=None, token=None, pickle=None, channel=None, hook=None):
    print ('checking url %s for channel %s' % ( url, channel) )
    notifier = SlackNotifier(type='set', token=token, pickle=pickle, channel=channel, hook=hook)
    notifier.notify_facet(facet='uri', value=url)

""" Watch for annotations by a user """
def notify_slack_user_activity(user=None, token=None, pickle=None, channel=None, hook=None):
    print ('checking user %s for channel %s' % ( user, channel) )
    notifier = SlackNotifier(type='dict', token=token, pickle=pickle, channel=channel, hook=hook)
    notifier.notify_facet(facet='user', value=user)

""" Watch for annotations in a Hypothesis group """
def notify_slack_group_activity(group=None, groupname=None, token=None, pickle=None, channel=None, hook=None):
    print ('checking group %s for channel %s' % ( groupname, channel) )
    notifier = SlackNotifier(type='set', token=token, pickle=pickle, channel=channel, hook=hook)
    notifier.notify_facet(facet='group', value=group, groupname=groupname)

""" Watch for annotations on a tag """
def notify_slack_tag_activity(tag=None, token=None, pickle=None, channel=None, hook=None):
    print ('checking tag %s for channel %s' % ( tag, channel) )
    notifier = SlackNotifier(type='set', token=token, pickle=pickle, channel=channel, hook=hook)
    notifier.notify_facet(facet='tag', value=tag)

# RSS recipies

def notify_rss_group_activity(group=None, groupname=None, token=None, pickle=None):
    print ('updating rss for group %s' % groupname )
    notifier = RssNotifier(type='set', token=token, pickle=pickle)
    notifier.notify_facet(facet='group', value=group, groupname=groupname)
    notifier.emit_group_rss(group=group, groupname=groupname)