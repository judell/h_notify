# Overview

This tool watches Hypothesis URLs, groups, tags, or users, and alerts on new annotation activity to Slack, email, or RSS.

See `examples.py` for recipes. To run a modified version of it, copy `hypothesis.py`, `h_notify.py`, and `examples.py` into a directory, adjust `examples.py` as needed, and run `python examples.py`.

The `pickle` argument to methods like `notify_slack_url_activity`, `notify_slack_group_activity`, `notify_email_tag_activity`, and `notify_rss_group_activity` names a file that's created, then updated, to remember the IDs of annotations already seen. So, for example, this call ...

 `notify_slack_url_activity(url='https://web.hypothes.is/*', token=default_token, pickle='urls', channel='test', hook=default_hook)`
 
 ... remembers IDs in `urls.pickle`.

## Slack

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

# RSS

The `pickle` argument in this case also names an XML file that contains an RSS feed. So, for example, given this call ...

`notify_rss_group_activity(group='8gk9i7VV', groupname='Anyone Can Join', token=default_token, pickle='8gk9i7VV')`

... the IDs are remembered in `8gk9i7VV.pickle` and the feed is generated into `8gk9i7VV.xml`. 

You'll need to host that file in some web-accessible location.


