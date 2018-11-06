Watch Hypothesis URLs, groups, tags, or users, alert on new activity to Slack, email, or RSS.

See examples.py for recipes.

To enable Slack @-mentions, create a file called `slack_namemap.json` like so:

```
{
  "https://hooks.slack.com/services/T03Q...gyzy" :
    {
    "@dave": "UC...DG",
    "@robertknight": "U0...30",
    "@dwhly": "U0...CT",
    "@hmstepanek": "U8...2W",
    "@judell": "U0...AV",
    "@nateangell": "U3...U9",
    "@arti": "U2...L4",
    "@heather": "U3...BEX",
    "@jeremydean": "U0...MK",
    "@katelyn": "U8...72",
    "@lyzadanger": "U8...R0",
    "@pfowler": "U0...GU",
    "@seanh": "U0...56",
    }
}```

The values are internal Slack IDs which you can find at `https://api.slack.com/methods/users.list/test`

Note that Slack usernames may be, but are not necessarily, the same as Hypothesis usernames. If I want to notify Dave Wolfe, whose Hypothesis username is dwolfe, I'll need to write his Slack handle, @dave, in the body of an annotation that's posted to a page monitored by this service.


