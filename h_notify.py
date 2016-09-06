import requests, json, traceback, sys 
from hypothesis import Hypothesis, HypothesisAnnotation
from operator import itemgetter
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

    def notify_facet(self, facet=None, value=None, groupname=None):
        params = {'_separate_replies':'true'}
        params[facet] = value
        #params['limit'] = 2
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
        anno_url = "https://hyp.is/%s" % anno.id
        quote = anno.exact if anno.exact is not None else ''
        type = 'annotation'
        if len(anno.references):
            ref = anno.references[0]
            anno_url = "https://hyp.is/%s" % ref
            type = 'reply'
        tags = ', '.join(anno.tags)
        ingroup = ''
        if anno.group is not '__world__':
            ingroup = 'in group %s' % groupname
        viewer = 'http://jonudell.net/h/facet.html?facet=user&search=' + anno.user # replace with Activity Pages when it's ready!
        if tags != '':
            tags = '*' + tags + '*\n'
        template = '<%s|%s> added by <%s|%s> to <%s|%s> %s\n>%s\n%s\n%s__________\n'
        payload = self.make_simple_payload(template % (anno_url, type, viewer, anno.user, anno.uri, anno.doc_title, ingroup, quote, anno.text, tags) )
        print (json.dumps(payload))
        r = requests.post(self.hook, data = json.dumps(payload))
        print ( r.status_code )

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

