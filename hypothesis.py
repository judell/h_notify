import json
import re
import requests
import time
import traceback

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

class Hypothesis:
    def __init__(self, username=None, token=None, limit=None, max_results=None, domain=None, host=None, port=None):
        if domain is None:
            self.domain = 'hypothes.is'
        else:
            self.domain = domain
        self.app_url = 'https://%s/app' % self.domain
        self.api_url = 'https://%s/api' % self.domain
        self.query_url = 'https://%s/api/search?{query}' % self.domain
        self.anno_url = 'https://%s/a' % domain
        self.via_url = 'https://via.hypothes.is'
        self.token = token
        self.username = username
        self.single_page_limit = 200 if limit is None else limit  # per-page, the api honors limit= up to (currently) 200
        self.multi_page_limit = 200 if max_results is None else max_results  # limit for paginated results
        if self.username is not None:
            self.permissions = {
                "read": ["group:__world__"],
                "update": ['acct:' + self.username + '@hypothes.is'],
                "delete": ['acct:' + self.username + '@hypothes.is'],
                "admin":  ['acct:' + self.username + '@hypothes.is']
                }
        else: self.permissions = {}

    def search(self, params={}):
        """ Call search API with no pagination, return rows """
        params['limit'] = self.single_page_limit
        h_url = self.query_url.format(query=urlencode(params))
        print ( h_url )
        json = requests.get(h_url).json()['rows']
        return json
 
    def search_all(self, params={}):
        """Call search API with pagination, return rows """
        params['offset'] = 0
        params['limit'] = self.single_page_limit
        while True:
            h_url = self.query_url.format(query=urlencode(params, True))
            print ( h_url )
            if self.token is not None:
                r = self.token_authenticated_query(h_url)
                obj = json.loads(r)
            else:
                r = requests.get(h_url)
                obj = json.loads(r.text)
            rows = obj['rows']
            row_count = len(rows)
            print ( "%s rows" % row_count )
            if 'replies' in obj:
               rows += obj['replies']
            row_count = len(rows)
            print ( "%s rows+replies" % row_count )
            params['offset'] += row_count
            if params['offset'] > self.multi_page_limit:
                break
            if len(rows) is 0:
                break
            for row in rows:
                yield row

    def token_authenticated_query(self, url=None):
        try:
           headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
           r = requests.get(url, headers=headers)
           return r.json()
        except:
            print ( traceback.print_exc() )

    def make_annotation_payload_with_target(self, url, start_pos, end_pos, prefix, exact, suffix, text, tags, link):
        """Create JSON payload for API call."""
        payload = {
            "uri": url,
            "user": 'acct:' + self.username + '@' + self.domain,
            "permissions": self.permissions,
            "target": 
            [{
                "scope": [url],
                "selector": 
                    [{
                        "start": start_pos,
                        "end": end_pos,
                        "type": "TextPositionSelector"
                        }, 
                        {
                        "type": "TextQuoteSelector", 
                        "prefix": prefix,
                        "exact": exact,
                        "suffix": suffix
                        },]
                }], 
            "tags": tags,
            "text": text
        }
        return payload

    def get_annotation(self, id=None):
        h_url = '%s/annotations/%s' % ( self.api_url, id )
        if self.token is not None:
            obj = self.token_authenticated_query(h_url)
        else:
            obj = json.loads(requests.get(h_url))
        return obj

    def create_annotation_with_target(self, url=None, start_pos=None, end_pos=None, prefix=None, 
                   exact=None, suffix=None, text=None, tags=None, link=None):
            """Call API with token and payload, create annotation"""
            payload = self.make_annotation_payload_with_target(url, start_pos, end_pos, prefix, exact, suffix, text, tags, link)
            r = self.post_annotation(payload)
            return r

    def make_annotation_payload_with_target_using_only_text_quote(self, url, prefix, exact, suffix, text, tags):
        """Create JSON payload for API call."""
        payload = {
            "uri": url,
            "user": 'acct:' + self.username + '@hypothes.is',
            "permissions": self.permissions,
            "target": 
            [{
                "scope": [url],
                "selector": 
                    [{
                        "type": "TextQuoteSelector", 
                        "prefix": prefix,
                        "exact": exact,
                        "suffix": suffix
                        },]
                }], 
            "tags": tags,
            "text": text
        }
        return payload

    def create_annotation_with_target_using_only_text_quote(self, url=None, prefix=None, 
               exact=None, suffix=None, text=None, tags=None):
        """Call API with token and payload, create annotation (using only text quote)"""
        payload = self.make_annotation_payload_with_target_using_only_text_quote(url, prefix, exact, suffix, text, tags)
        r = self.post_annotation(payload)
        return r

    def create_annotation_with_custom_payload(self, payload=None):
        payload = json.loads(payload)
        r = self.post_annotation(payload)
        return r

    def post_annotation(self, payload):
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
        data = json.dumps(payload, ensure_ascii=False)
        r = requests.post(self.api_url + '/annotations', headers=headers, data=data)
        return r

    def update_annotation(self, id, payload):
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
        data = json.dumps(payload, ensure_ascii=False)
        r = requests.put(self.api_url + '/annotations/' + id, headers=headers, data=data)
        return r
    
    def delete_annotation(self, id):
       headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
       r = requests.delete(self.api_url + '/annotations/' + id, headers=headers)
       return r    


class HypothesisAnnotation:
    """Encapsulate one row of a Hypothesis API search."""   
    def __init__(self, row):
        self.type = None
        self.id = row['id']
        self.group = row['group']
        self.updated = row['updated'][0:19]
        self.permissions = row['permissions']
        self.user = row['user'].replace('acct:','').replace('@hypothes.is','')
        self.is_group = self.group not in [None, '__world__', 'NoGroup']
        self.is_world_private = not self.is_group and 'group:__world__' not in self.permissions['read']
        self.is_group_private = self.is_group and 'group:'+self.group not in self.permissions['read']
        self.is_public = not self.is_group and not self.is_group_private and not self.is_world_private

        if 'uri' in row:    # is it ever not?
            self.uri = row['uri']
        else:
             self.uri = "no uri field for %s" % self.id
        self.uri = self.uri.replace('https://via.hypothes.is/h/','').replace('https://via.hypothes.is/','')

        if self.uri.startswith('urn:x-pdf') and 'document' in row:
            if 'link' in row['document']:
                self.links = row['document']['link']
                for link in self.links:
                    self.uri = link['href']
                    if self.uri.startswith('urn:') == False:
                        break
            if self.uri.startswith('urn:') and 'filename' in row['document']:
                self.uri = row['document']['filename']

        if 'document' in row and 'title' in row['document']:
            t = row['document']['title']
            if isinstance(t, list) and len(t):
                self.doc_title = t[0]
            else:
                self.doc_title = t
        else:
            self.doc_title = None
        if self.doc_title is None:
            self.doc_title = ''
        self.doc_title = self.doc_title.replace('"',"'")
        if self.doc_title == '': self.doc_title = 'untitled'

        self.tags = []
        if 'tags' in row and row['tags'] is not None:
            self.tags = row['tags']
            if isinstance(self.tags, list):
                self.tags = [t.strip() for t in self.tags]

        self.text = ''
        if 'text' in row:
            self.text = row['text']

        self.references = []
        if 'references' in row:
            self.type = 'reply'
            self.references = row['references']

        self.target = []
        if 'target' in row:
            self.target = row['target']

        self.is_page_note = False
        try:
            if self.references == [] and self.target is not None and len(self.target) and isinstance(self.target, list) and not 'selector' in self.target[0]:
                self.is_page_note = True
                self.type = 'pagenote'
        except:
            traceback.print_exc()
        if 'document' in row and 'link' in row['document']:
            self.links = row['document']['link']
            if not isinstance(self.links, list):
                self.links = [{'href':self.links}]
        else:
            self.links = []

        self.start = self.end = self.prefix = self.exact = self.suffix = None
        try:
            if isinstance(self.target,list) and len(self.target) and 'selector' in self.target[0]:
                self.type = 'annotation'
                selectors = self.target[0]['selector']
                for selector in selectors:
                    if 'type' in selector and selector['type'] == 'TextQuoteSelector':
                        try:
                            self.prefix = selector['prefix']
                            self.exact = selector['exact']
                            self.suffix = selector['suffix']
                        except:
                            traceback.print_exc()
                    if 'type' in selector and selector['type'] == 'TextPositionSelector' and 'start' in selector:
                        self.start = selector['start']
                        self.end = selector['end']
                    if 'type' in selector and selector['type'] == 'FragmentSelector' and 'value' in selector:
                        self.fragment_selector = selector['value']
        except:
            print ( traceback.format_exc() )
