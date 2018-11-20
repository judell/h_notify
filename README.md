# Overview

This tool watches Hypothesis URLs, groups, tags, or users, and alerts on new annotation activity to Slack, email, or RSS. It runs as a standalone Python program, ideally on a server, but alternatively on an always-connected desktop computer. It periodically queries the Hypothesis API along one or more axes -- url (or wildcard_uri), user, group, tag -- and sends notifications by way of Slack, email, or RSS.

See `examples.py` for recipes. To run a modified version of it, copy `hypothesis.py`, `h_notify.py`, and `examples.py` into a directory, adjust `examples.py` as needed, and run `python examples.py`.

The `pickle` argument to methods like `notify_slack_url_activity`, `notify_slack_group_activity`, `notify_email_tag_activity`, and `notify_rss_group_activity` names a file that's created, then updated, to remember the IDs of annotations already seen. So, for example, this call ...

 `notify_slack_url_activity(url='https://web.hypothes.is/*', token=default_token, pickle='urls', channel='test', hook=default_hook)`
 
 ... remembers IDs in `urls.pickle`.

## Slack

### Web hook

You'll need an "incoming web hook" which you create in Slack: https://api.slack.com/incoming-webhooks

### @-mentions

To enable Slack @-mentions, create a file called `slack_namemap.json` like so:

```
{
  "https://hooks.slack.com/services/T03Q...gyzy" :
    {
    "@dave": "UC...DG",
    "@dwhly": "U0...CT",
    "@hmstepanek": "U8...2W",
    "@judell": "U0...AV",
    "@nateangell": "U3...U9",
    "@katelyn": "U8...72",
    }
}
```

The values are internal Slack IDs which you can find at `https://api.slack.com/methods/users.list/test`

Note that Slack usernames may be, but are not necessarily, the same as Hypothesis usernames. If I want to notify Dave Wolfe, whose Hypothesis username is dwolfe, I'll need to write his Slack handle, @dave, in the body of an annotation that's posted to a page monitored by this service.

## RSS

RSS feeds are inherently unauthenticated, but access to Hypothesis private annotations requires authentication, so you can't use https://hypothes.is/stream.rss or https://hypothes.is/stream.atom to receive feeds of private annotation activity.

This tool authenticates to the Hypothesis API and produces XML files that you can then serve to RSS readers at unauthenticated-but-secret URLs. You will, however, need to host those files where RSS readers can get them.

The `pickle` argument in this case also names an XML file that contains an RSS feed. So, for example, given this call ...

`notify_rss_group_activity(group='8gk9i7VV', groupname='Anyone Can Join', token=default_token, pickle='8gk9i7VV')`

... the IDs are remembered in `8gk9i7VV.pickle` and the feed is generated into `8gk9i7VV.xml`.

## email

You'll need to set up credentials like so:

```
default_smtp_server = 'smtp.example.com' 
default_email_sender = 'hypothesis.notifier@example.com'
default_email_password = 'q1...Nm'
```




