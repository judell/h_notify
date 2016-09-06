from h_notify import *
import time

default_token = '687...3df5' # hypothesis api token for a user who is a member of all monitored groups
default_hook = 'https://hooks.slack.com/services/T03...yzy' # see https://YOUR_VANITY_NAME.slack.com/apps/manage/custom-integrations)

while True:
    try:
        # notify when an url in a list of urls of interest to the team is annotated
        urls = ['http://example.com', 'https://hypothes.is/blog/test-our-new-canvas-app-prototype/']
        for url in urls:
            notify_slack_url_activity(url=url, token=default_token, pickle='urls', channel='test', hook=default_hook)

        # notify when there's an annotation from one among a list of users
        users = ['remiholden', 'jeremydean']
        for user in users:
            notify_slack_user_activity(user=user, token=default_token, pickle='users', channel='test', hook=default_hook) 

        # notify when there's an annotation in a group
        notify_slack_group_activity(group='8gk9i7VV', groupname='Anyone Can Join', token=default_token, pickle='AnyoneCanJoin', channel='test', hook=default_hook)

        # notify when there's an annotation with a specified tag
        notify_slack_tag_activity(tag='nextprez', token=default_token, pickle='nextprez', channel='test', hook=default_hook)

        print ( 'sleeping' )
        time.sleep(60 * 30)  # wait 30 min to be polite to the hypothesis api
    except:
        print ( traceback.print_exc() )